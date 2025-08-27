// ========== MOBILE MENU TOGGLE ==========
document.getElementById('mobile-menu-btn').addEventListener('click', () => {
    document.getElementById('nav-menu').classList.toggle('active');
});

// ========== SMOOTH SCROLLING FOR NAVIGATION ==========
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
        document.getElementById('nav-menu').classList.remove('active'); // close mobile menu
    });
});

// ========== FAQ TOGGLE FUNCTION ==========
function toggleFAQ(element) {
    const answer = element.nextElementSibling;
    const icon = element.querySelector('span');

    // close other open FAQs
    document.querySelectorAll('.faq-answer.active').forEach(item => {
        if (item !== answer) item.classList.remove('active');
    });
    document.querySelectorAll('.faq-question span').forEach(span => {
        if (span !== icon) span.textContent = '+';
    });

    // toggle selected FAQ
    if (answer.classList.contains('active')) {
        answer.classList.remove('active');
        icon.textContent = '+';
    } else {
        answer.classList.add('active');
        icon.textContent = '-';
    }
}
window.toggleFAQ = toggleFAQ; // make available to inline onclick

// ========== AI DIET PLAN GENERATOR ==========
document.getElementById('diet-form').addEventListener('submit', async function (e) {
    e.preventDefault();

    const formData = new FormData(this);
    const userData = Object.fromEntries(formData);

    // Show loading spinner
    document.getElementById('btn-text').textContent = 'Generating...';
    document.getElementById('btn-loading').style.display = 'inline-block';
    document.getElementById('generate-btn').disabled = true;

    // Simulate AI delay
    await new Promise(resolve => setTimeout(resolve, 2000));

    // Calculate BMI
    const heightM = userData.height / 100;
    const bmi = (userData.weight / (heightM * heightM)).toFixed(1);

    // Calculate BMR and calories
    let bmr;
    if (userData.gender === 'male') {
        bmr = 88.362 + (13.397 * userData.weight) + (4.799 * userData.height) - (5.677 * userData.age);
    } else {
        bmr = 447.593 + (9.247 * userData.weight) + (3.098 * userData.height) - (4.330 * userData.age);
    }
    const dailyCalories = Math.round(bmr * 1.5); // assume moderate activity

    // Prepare recommendations
    let recs = [];
    if (userData.smoking === 'yes') recs.push("⚠️ Reduce or quit smoking for better cardiovascular health.");
    if (userData.drinking === 'yes') recs.push("⚠️ Limit alcohol intake to aid recovery and metabolism.");

    // Determine BMI category
    let bmiStatus = '';
    if (bmi < 18.5) bmiStatus = "Underweight - Focus on healthy weight gain";
    else if (bmi < 25) bmiStatus = "Normal - Maintain your weight";
    else if (bmi < 30) bmiStatus = "Overweight - Aim for gradual weight loss";
    else bmiStatus = "Obese - Seek professional guidance";

    // Generate weekly plan HTML
    const dietHTML = buildDietPlan(userData.name, bmi, bmiStatus, dailyCalories, recs);

    // Show result
    document.getElementById('diet-content').innerHTML = dietHTML;
    document.getElementById('ai-diet-result').style.display = 'block';
    document.getElementById('ai-diet-result').scrollIntoView({ behavior: 'smooth' });

    // Reset button
    document.getElementById('btn-text').textContent = 'Generate AI Diet Plan';
    document.getElementById('btn-loading').style.display = 'none';
    document.getElementById('generate-btn').disabled = false;
});

function buildDietPlan(name, bmi, bmiStatus, calories, recs) {
    const days = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'];
    const mealCalories = {
        breakfast: Math.round(calories * 0.25),
        snack: Math.round(calories * 0.1),
        lunch: Math.round(calories * 0.3),
        evening: Math.round(calories * 0.1),
        dinner: Math.round(calories * 0.25),
    };

    let html = `
    <div class="user-summary">
        <h4>Hello ${name}! 👋</h4>
        <div class="user-stats">
            <div class="stat-item"><strong>BMI:</strong> ${bmi}</div>
            <div class="stat-item"><strong>Status:</strong> ${bmiStatus}</div>
            <div class="stat-item"><strong>Calories:</strong> ~${calories} kcal/day</div>
        </div>
    </div>
    `;

    if (recs.length) {
        html += `<div class="recommendations">
            <h4>Lifestyle Recommendations</h4>
            ${recs.map(r => `<div class="recommendation-item warning">${r}</div>`).join('')}
        </div>`;
    }

    html += `<div class="weekly-plan">`;
    days.forEach(day => {
        html += `
        <div class="day-plan">
            <div class="day-title">${day}</div>
            <div class="meals-grid">
                ${mealBlock('Breakfast','Oats with milk, fruits, boiled eggs',mealCalories.breakfast)}
                ${mealBlock('Mid-morning Snack','Handful of nuts / yogurt',mealCalories.snack)}
                ${mealBlock('Lunch','Brown rice, dal, veggies, chicken/fish',mealCalories.lunch)}
                ${mealBlock('Evening Snack','Green tea & sprouts',mealCalories.evening)}
                ${mealBlock('Dinner','Chapati, paneer/lean meat, salad',mealCalories.dinner)}
            </div>
        </div>
        `;
    });
    html += `</div>`;

    html += `<div class="recommendations">
        <div class="recommendation-item advice">
            💡 Drink 8-10 glasses of water daily, sleep 7-8 hours, and exercise regularly.
        </div>
    </div>`;

    return html;
}

function mealBlock(name, desc, cal) {
    return `
    <div class="meal-item">
        <div class="meal-name">${name}</div>
        <div class="meal-description">${desc}</div>
        <div class="meal-calories">${cal} kcal</div>
    </div>
    `;
}
