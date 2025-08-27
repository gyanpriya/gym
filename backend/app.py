from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import os
import requests
import json
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Hugging Face API configuration
HUGGINGFACE_API_TOKEN = os.getenv('HUGGINGFACE_API_TOKEN')
HUGGINGFACE_API_URL = "https://api-inference.huggingface.co/models/"

class DietPlanGenerator:
    def __init__(self):
        # Using free models from Hugging Face
        self.model_name = "microsoft/DialoGPT-medium"  # Free conversational AI
        self.headers = {
            "Authorization": f"Bearer {HUGGINGFACE_API_TOKEN}",
            "Content-Type": "application/json"
        }
    
    def calculate_bmr(self, weight, height, age, gender):
        """Calculate Basal Metabolic Rate"""
        if gender.lower() == 'male':
            bmr = 88.362 + (13.397 * weight) + (4.799 * height) - (5.677 * age)
        else:
            bmr = 447.593 + (9.247 * weight) + (3.098 * height) - (4.330 * age)
        return round(bmr)
    
    def calculate_bmi(self, weight, height):
        """Calculate Body Mass Index"""
        height_m = height / 100
        bmi = weight / (height_m ** 2)
        return round(bmi, 1)
    
    def get_bmi_category(self, bmi):
        """Get BMI category and recommendations"""
        if bmi < 18.5:
            return "Underweight", "Focus on healthy weight gain with nutrient-dense foods"
        elif bmi < 25:
            return "Normal Weight", "Maintain current weight with balanced nutrition"
        elif bmi < 30:
            return "Overweight", "Focus on gradual weight loss through caloric deficit"
        else:
            return "Obese", "Consult healthcare provider, focus on sustainable weight loss"
    
    async def generate_ai_diet_plan(self, user_data):
        """Generate diet plan using Hugging Face LLM"""
        try:
            # Calculate user metrics
            bmr = self.calculate_bmr(
                user_data['weight'], 
                user_data['height'], 
                user_data['age'], 
                user_data['gender']
            )
            bmi = self.calculate_bmi(user_data['weight'], user_data['height'])
            bmi_category, bmi_advice = self.get_bmi_category(bmi)
            
            # Daily calories (BMR * activity factor)
            daily_calories = round(bmr * 1.5)  # Moderate activity
            
            # Create detailed prompt for AI
            prompt = f"""Create a detailed 7-day diet plan for:
            Name: {user_data['name']}
            Age: {user_data['age']} years
            Gender: {user_data['gender']}
            Weight: {user_data['weight']} kg
            Height: {user_data['height']} cm
            BMI: {bmi} ({bmi_category})
            Daily Calories: {daily_calories}
            Smoking: {user_data['smoking']}
            Drinking: {user_data['drinking']}
            
            Please provide:
            1. Daily meal schedule with specific foods
            2. Portion sizes and nutritional focus
            3. Pre/post workout meals
            4. Hydration recommendations
            5. Lifestyle-specific advice based on smoking/drinking habits
            
            Format as a structured weekly plan with breakfast, lunch, dinner, and snacks for each day."""
            
            # Call Hugging Face API
            api_url = f"{HUGGINGFACE_API_URL}microsoft/DialoGPT-medium"
            
            payload = {
                "inputs": prompt,
                "parameters": {
                    "max_length": 1000,
                    "temperature": 0.7,
                    "do_sample": True
                }
            }
            
            response = requests.post(api_url, headers=self.headers, json=payload)
            
            if response.status_code == 200:
                ai_response = response.json()
                
                # If model is loading, wait and retry
                if isinstance(ai_response, dict) and "estimated_time" in ai_response:
                    logger.info(f"Model loading, estimated time: {ai_response['estimated_time']} seconds")
                    return self.generate_fallback_plan(user_data, bmr, bmi, bmi_category, daily_calories)
                
                # Extract generated text
                if isinstance(ai_response, list) and len(ai_response) > 0:
                    generated_text = ai_response[0].get('generated_text', '')
                else:
                    generated_text = str(ai_response)
                
                # Format the response
                return self.format_ai_response(user_data, generated_text, bmr, bmi, bmi_category, daily_calories)
            
            else:
                logger.error(f"API error: {response.status_code} - {response.text}")
                return self.generate_fallback_plan(user_data, bmr, bmi, bmi_category, daily_calories)
                
        except Exception as e:
            logger.error(f"Error generating AI diet plan: {str(e)}")
            return self.generate_fallback_plan(user_data, bmr, bmi, bmi_category, daily_calories)
    
    def generate_fallback_plan(self, user_data, bmr, bmi, bmi_category, daily_calories):
        """Generate a structured diet plan when AI fails"""
        
        # Macro distribution
        protein_cals = daily_calories * 0.25
        carb_cals = daily_calories * 0.45
        fat_cals = daily_calories * 0.30
        
        protein_grams = round(protein_cals / 4)
        carb_grams = round(carb_cals / 4)
        fat_grams = round(fat_cals / 9)
        
        # Weekly meal plan
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        
        meal_plan = {
            'user_info': {
                'name': user_data['name'],
                'age': user_data['age'],
                'gender': user_data['gender'],
                'weight': user_data['weight'],
                'height': user_data['height'],
                'bmi': bmi,
                'bmi_category': bmi_category,
                'daily_calories': daily_calories,
                'macros': {
                    'protein': f"{protein_grams}g",
                    'carbs': f"{carb_grams}g",
                    'fats': f"{fat_grams}g"
                }
            },
            'weekly_plan': {},
            'recommendations': self.get_lifestyle_recommendations(user_data),
            'general_tips': [
                "Drink 8-10 glasses of water daily",
                "Eat every 3-4 hours to maintain metabolism",
                "Include protein in every meal for muscle recovery",
                "Choose complex carbohydrates over simple sugars",
                "Eat your largest meal 2-3 hours before workouts",
                "Have a post-workout meal within 30 minutes",
                "Limit processed foods and added sugars"
            ]
        }
        
        # Generate daily meal plans
        for day in days:
            meal_plan['weekly_plan'][day] = self.generate_daily_meals(daily_calories, user_data)
        
        return meal_plan
    
    def generate_daily_meals(self, daily_calories, user_data):
        """Generate meals for a single day"""
        
        # Meal calorie distribution
        breakfast_cals = round(daily_calories * 0.25)
        snack1_cals = round(daily_calories * 0.10)
        lunch_cals = round(daily_calories * 0.30)
        snack2_cals = round(daily_calories * 0.10)
        dinner_cals = round(daily_calories * 0.25)
        
        # Sample meal options (can be randomized)
        breakfast_options = [
            "Oatmeal with banana and almonds",
            "Greek yogurt with berries and granola",
            "Scrambled eggs with whole grain toast",
            "Protein smoothie with spinach and fruits"
        ]
        
        lunch_options = [
            "Grilled chicken with quinoa and vegetables",
            "Lentil curry with brown rice",
            "Fish with sweet potato and broccoli",
            "Chickpea salad with mixed greens"
        ]
        
        dinner_options = [
            "Lean beef with roasted vegetables",
            "Salmon with asparagus and wild rice",
            "Turkey meatballs with zucchini noodles",
            "Tofu stir-fry with brown rice"
        ]
        
        snack_options = [
            "Apple with almond butter",
            "Mixed nuts and dried fruits",
            "Greek yogurt with honey",
            "Protein bar or shake"
        ]
        
        import random
        
        return {
            'breakfast': {
                'meal': random.choice(breakfast_options),
                'calories': breakfast_cals
            },
            'morning_snack': {
                'meal': random.choice(snack_options),
                'calories': snack1_cals
            },
            'lunch': {
                'meal': random.choice(lunch_options),
                'calories': lunch_cals
            },
            'afternoon_snack': {
                'meal': random.choice(snack_options),
                'calories': snack2_cals
            },
            'dinner': {
                'meal': random.choice(dinner_options),
                'calories': dinner_cals
            }
        }
    
    def get_lifestyle_recommendations(self, user_data):
        """Get personalized recommendations based on lifestyle"""
        recommendations = []
        
        if user_data['smoking'] == 'yes':
            recommendations.append({
                'type': 'warning',
                'message': 'Smoking reduces oxygen delivery to muscles. Consider quitting for better workout performance and recovery.'
            })
            recommendations.append({
                'type': 'advice',
                'message': 'Increase Vitamin C intake (citrus fruits, bell peppers) to combat oxidative stress from smoking.'
            })
        
        if user_data['drinking'] == 'yes':
            recommendations.append({
                'type': 'warning',
                'message': 'Alcohol can interfere with muscle protein synthesis and recovery. Limit intake, especially around workout times.'
            })
            recommendations.append({
                'type': 'advice',
                'message': 'If you drink, ensure adequate hydration and consider B-complex vitamins to support metabolism.'
            })
        
        # Age-specific recommendations
        age = int(user_data['age'])
        if age < 25:
            recommendations.append({
                'type': 'info',
                'message': 'Focus on building healthy eating habits early. Your metabolism is naturally higher at this age.'
            })
        elif age > 40:
            recommendations.append({
                'type': 'info',
                'message': 'Prioritize protein intake and calcium for bone health. Consider adding resistance training.'
            })
        
        return recommendations
    
    def format_ai_response(self, user_data, ai_text, bmr, bmi, bmi_category, daily_calories):
        """Format AI response into structured data"""
        # This would parse the AI response and structure it
        # For now, combining AI insights with structured data
        
        return {
            'user_info': {
                'name': user_data['name'],
                'bmi': bmi,
                'bmi_category': bmi_category,
                'daily_calories': daily_calories,
            },
            'ai_insights': ai_text[:500] + "..." if len(ai_text) > 500 else ai_text,
            'structured_plan': self.generate_fallback_plan(user_data, bmr, bmi, bmi_category, daily_calories)
        }

# Initialize diet plan generator
diet_generator = DietPlanGenerator()

@app.route('/')
def index():
    """Serve the main website"""
    # Read the frontend HTML file
    try:
        with open('frontend/index.html', 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Everytime Fitness - Setup Required</title>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body style="font-family: Arial, sans-serif; padding: 20px; text-align: center;">
            <h1>🏋️‍♂️ Everytime Fitness</h1>
            <p>Backend is running! Please set up the frontend files.</p>
            <p>API endpoint available at: <code>/api/generate-diet-plan</code></p>
        </body>
        </html>
        """

@app.route('/api/generate-diet-plan', methods=['POST'])
def generate_diet_plan():
    """Generate personalized diet plan using AI"""
    try:
        # Get user data from request
        user_data = request.get_json()
        
        # Validate required fields
        required_fields = ['name', 'age', 'height', 'weight', 'gender', 'smoking', 'drinking']
        for field in required_fields:
            if field not in user_data:
                return jsonify({
                    'error': f'Missing required field: {field}',
                    'success': False
                }), 400
        
        # Generate diet plan using AI
        import asyncio
        diet_plan = asyncio.run(diet_generator.generate_ai_diet_plan(user_data))
        
        return jsonify({
            'success': True,
            'data': diet_plan,
            'message': 'Diet plan generated successfully!'
        })
        
    except Exception as e:
        logger.error(f"Error in generate_diet_plan: {str(e)}")
        return jsonify({
            'error': 'Failed to generate diet plan. Please try again.',
            'success': False
        }), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'message': 'Everytime Fitness API is running!',
        'ai_model': 'Hugging Face - Microsoft DialoGPT',
        'features': ['Diet Plan Generation', 'BMI Calculator', 'Lifestyle Recommendations']
    })

@app.route('/api/bmi-calculator', methods=['POST'])
def calculate_bmi():
    """Calculate BMI and provide basic recommendations"""
    try:
        data = request.get_json()
        weight = float(data['weight'])
        height = float(data['height'])
        
        bmi = diet_generator.calculate_bmi(weight, height)
        category, advice = diet_generator.get_bmi_category(bmi)
        
        return jsonify({
            'success': True,
            'bmi': bmi,
            'category': category,
            'advice': advice
        })
        
    except Exception as e:
        return jsonify({
            'error': 'Invalid input data',
            'success': False
        }), 400

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=os.getenv('DEBUG', 'False').lower() == 'true')