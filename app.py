from flask import Flask, render_template, request
import sqlite3
import json
from datetime import datetime

app = Flask(__name__)
DATABASE = 'database.db'

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    db = get_db()
    db.execute('''
        CREATE TABLE IF NOT EXISTS diet_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT, age INTEGER, weight REAL, height REAL,
            gender TEXT, goal TEXT, activity TEXT,
            bmi REAL, calories INTEGER, plan TEXT, created TEXT
        )
    ''')
    db.commit()
    db.close()

def calc_bmi(weight_kg, height_cm):
    h = height_cm / 100
    return round(weight_kg / (h * h), 1)

def bmi_category(bmi):
    if bmi < 18.5: return "Underweight"
    if bmi < 25:   return "Normal weight"
    if bmi < 30:   return "Overweight"
    return "Obese"

def calc_calories(age, weight, height, gender, activity, goal):
    if gender == 'male':
        bmr = 10 * weight + 6.25 * height - 5 * age + 5
    else:
        bmr = 10 * weight + 6.25 * height - 5 * age - 161
    multipliers = {
        'sedentary': 1.2, 'light': 1.375,
        'moderate': 1.55, 'active': 1.725, 'very_active': 1.9
    }
    tdee = bmr * multipliers.get(activity, 1.55)
    if goal == 'lose': return int(tdee - 500)
    if goal == 'gain': return int(tdee + 400)
    return int(tdee)

MEAL_PLANS = {
    'lose': {
        'title': 'Fat-Loss Plan',
        'description': 'High protein, calorie-deficit meals to shed fat while preserving muscle.',
        'meals': [
            {'name': 'Breakfast',     'items': ['Oats with skim milk & berries', 'Boiled eggs (2)', 'Green tea']},
            {'name': 'Mid-Morning',   'items': ['Apple or pear', 'A handful of almonds']},
            {'name': 'Lunch',         'items': ['Grilled chicken breast (150g)', 'Brown rice', 'Steamed broccoli']},
            {'name': 'Evening Snack', 'items': ['Low-fat Greek yogurt', 'Cucumber sticks']},
            {'name': 'Dinner',        'items': ['Baked salmon or paneer (120g)', 'Quinoa salad', 'Lemon greens']},
        ],
        'tips': ['Drink 3+ litres of water daily', 'Avoid sugary drinks', 'Sleep 7-8 hours']
    },
    'gain': {
        'title': 'Muscle-Gain Plan',
        'description': 'Calorie-surplus, protein-rich meals to support muscle growth.',
        'meals': [
            {'name': 'Breakfast',     'items': ['Banana oat smoothie', 'Whole eggs (3) scrambled', 'Whole-grain toast']},
            {'name': 'Mid-Morning',   'items': ['Protein shake with milk', 'Mixed nuts & dates']},
            {'name': 'Lunch',         'items': ['Chicken curry', 'Rice (1 cup)', 'Roti (2)', 'Curd']},
            {'name': 'Evening Snack', 'items': ['Cheese sandwich', 'Banana', 'Full-fat milk']},
            {'name': 'Dinner',        'items': ['Grilled chicken (200g)', 'Sweet potato', 'Sauteed vegetables']},
        ],
        'tips': ['Eat every 3 hours', 'Post-workout protein within 30 min', 'Progressive overload + rest']
    },
    'maintain': {
        'title': 'Maintenance Plan',
        'description': 'Balanced meals to sustain your current weight and energy.',
        'meals': [
            {'name': 'Breakfast',     'items': ['Idli / dosa with sambar', 'Fresh fruit bowl', 'Black coffee']},
            {'name': 'Mid-Morning',   'items': ['Roasted chana', 'Seasonal fruit']},
            {'name': 'Lunch',         'items': ['Dal + 2 rotis', 'Sabzi', 'Salad + buttermilk']},
            {'name': 'Evening Snack', 'items': ['Sprouts chaat', 'Herbal tea']},
            {'name': 'Dinner',        'items': ['Khichdi / soup', 'Grilled protein (100g)', 'Stir-fried greens']},
        ],
        'tips': ['Balance macros: 40% carbs, 30% protein, 30% fats', '5 servings of vegetables daily', 'Moderate exercise daily']
    }
}

def get_plan(goal):
    return MEAL_PLANS.get(goal, MEAL_PLANS['maintain'])

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate():
    name     = request.form.get('name', 'User')
    age      = int(request.form.get('age', 25))
    weight   = float(request.form.get('weight', 70))
    height   = float(request.form.get('height', 170))
    gender   = request.form.get('gender', 'male')
    goal     = request.form.get('goal', 'maintain')
    activity = request.form.get('activity', 'moderate')

    bmi      = calc_bmi(weight, height)
    category = bmi_category(bmi)
    calories = calc_calories(age, weight, height, gender, activity, goal)
    plan     = get_plan(goal)

    db = get_db()
    db.execute(
        'INSERT INTO diet_logs (name,age,weight,height,gender,goal,activity,bmi,calories,plan,created) VALUES (?,?,?,?,?,?,?,?,?,?,?)',
        (name, age, weight, height, gender, goal, activity, bmi, calories,
         json.dumps(plan), datetime.now().strftime('%Y-%m-%d %H:%M'))
    )
    db.commit()
    db.close()

    return render_template('result.html',
        name=name, age=age, weight=weight, height=height,
        gender=gender, goal=goal, activity=activity,
        bmi=bmi, category=category, calories=calories, plan=plan
    )

@app.route('/diet_plan')
def diet_plan():
    db = get_db()
    logs = db.execute('SELECT * FROM diet_logs ORDER BY created DESC LIMIT 20').fetchall()
    db.close()
    return render_template('diet_plan.html', logs=logs)

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
