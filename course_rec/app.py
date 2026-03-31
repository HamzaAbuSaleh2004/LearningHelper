"""
Course Recommendation System — Flask Application
Unified engine: SBERT for semantic search + RL weighting for personalized recommendations.
Bilingual support (EN/AR), testing system, and course scraping.
"""

import json
import math
import os
import sys
import uuid
from datetime import datetime, timedelta
from functools import wraps

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
    jsonify,
)

from scraper import load_courses_cache, start_scraper_thread, run_scraper

# ── SBERT Integration (from existing src/ project) ───────────────
# Add the src directory to path so we can import the SBERT recommender
SRC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
sys.path.insert(0, os.path.abspath(SRC_DIR))

sbert_engine = None
try:
    from recommender import CourseRecommender
    print("⏳ Loading SBERT Model for semantic search...")
    sbert_engine = CourseRecommender()
    print("✅ SBERT Model Loaded! Semantic search is available.")
except Exception as e:
    print(f"⚠️  SBERT not available (running without semantic search): {e}")
    print("   The app will work using category-based recommendations only.")
    sbert_engine = None

# ══════════════════════════════════════════════════════════════════
# APP SETUP
# ══════════════════════════════════════════════════════════════════
app = Flask(__name__)
app.secret_key = "course_rec_secret_key_2026"
app.config["JSON_AS_ASCII"] = False

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, "db.json")

# ══════════════════════════════════════════════════════════════════
# CATEGORIES
# ══════════════════════════════════════════════════════════════════
CATEGORIES = [
    "programming",
    "data_science",
    "web_development",
    "ai_ml",
    "design",
    "business",
    "language",
]

CATEGORY_DISPLAY = {
    "en": {
        "programming": "Programming",
        "data_science": "Data Science",
        "web_development": "Web Development",
        "ai_ml": "AI & Machine Learning",
        "design": "Design",
        "business": "Business",
        "language": "Languages",
        "linux": "Linux & IT",
    },
    "ar": {
        "programming": "البرمجة",
        "data_science": "علم البيانات",
        "web_development": "تطوير الويب",
        "ai_ml": "الذكاء الاصطناعي",
        "design": "التصميم",
        "business": "الأعمال",
        "language": "اللغات",
        "linux": "لينكس",
    },
}

CATEGORY_ICONS = {
    "programming": "fa-code",
    "data_science": "fa-chart-bar",
    "web_development": "fa-globe",
    "ai_ml": "fa-robot",
    "design": "fa-palette",
    "business": "fa-briefcase",
    "language": "fa-language",
    "linux": "fa-terminal",
}

# ══════════════════════════════════════════════════════════════════
# TRANSLATIONS
# ══════════════════════════════════════════════════════════════════
TRANSLATIONS = {
    "en": {
        "app_name": "LearnPath AI",
        "app_tagline": "Your Intelligent Course Navigator",
        "nav_home": "Home",
        "nav_onboard": "Get Started",
        "nav_courses": "Courses",
        "nav_recommend": "For You",
        "nav_search": "AI Search",
        "nav_test": "Assessment",
        "nav_benefit": "Progress",
        "nav_lang": "العربية",
        "hero_title": "Discover Your Perfect",
        "hero_title_highlight": "Learning Path",
        "hero_subtitle": "AI-powered course recommendations tailored to your goals, level, and interests. Start your journey today.",
        "hero_cta": "Start Your Journey",
        "hero_explore": "Explore Courses",
        "search_title": "AI-Powered Course Search",
        "search_subtitle": "Use our SBERT semantic engine to find courses that match your exact intent.",
        "search_placeholder_ai": "e.g. I want to learn Python for Data Science...",
        "search_results_for": "Results for",
        "search_no_results": "No matching courses found. Try a different query.",
        "search_match": "Match",
        "search_sbert_badge": "SBERT Semantic Search",
        "search_unavailable": "Semantic search is not available. Please use the course catalog.",
        "stats_courses": "Courses Available",
        "stats_categories": "Categories",
        "stats_platforms": "Platforms",
        "stats_users": "Active Learners",
        "onboard_title": "Create Your Profile",
        "onboard_subtitle": "Tell us about yourself and we'll personalize your learning experience.",
        "field_name": "Full Name",
        "field_email": "Email Address",
        "field_level": "Study Level",
        "field_goals": "Learning Goals",
        "field_name_placeholder": "Enter your full name",
        "field_email_placeholder": "your.email@example.com",
        "level_beginner": "Beginner",
        "level_intermediate": "Intermediate",
        "level_advanced": "Advanced",
        "btn_submit": "Create Profile",
        "btn_continue": "Continue",
        "btn_back": "Back",
        "btn_retake": "Retake Test",
        "btn_start_test": "Start Assessment",
        "btn_view_results": "View Results",
        "btn_rate": "Submit Rating",
        "btn_scrape": "Refresh Courses",
        "test_title": "Knowledge Assessment",
        "test_subtitle_pre": "Pre-Course Assessment — Let's see where you stand.",
        "test_subtitle_post": "Post-Course Assessment — Let's measure your growth.",
        "test_question": "Question",
        "test_of": "of",
        "test_submit": "Submit Answers",
        "result_title": "Assessment Results",
        "result_score": "Your Score",
        "result_correct": "Correct Answers",
        "result_total": "Total Questions",
        "result_pre_done": "Pre-test completed! Explore courses and come back for the post-test.",
        "result_post_done": "Post-test completed! Check your progress dashboard.",
        "benefit_title": "Learning Progress",
        "benefit_subtitle": "Track your growth with pre and post assessment comparison.",
        "benefit_pre": "Pre-Test Score",
        "benefit_post": "Post-Test Score",
        "benefit_delta": "Improvement",
        "benefit_no_tests": "Complete both pre and post tests to see your progress.",
        "recommend_title": "Recommended For You",
        "recommend_subtitle": "Courses tailored to your interests and learning weights.",
        "recommend_empty": "Complete your profile first to get personalized recommendations.",
        "recommend_based_on": "Based on your interest in",
        "feedback_title": "Rate This Course",
        "feedback_subtitle": "Your feedback helps us improve recommendations.",
        "feedback_thanks": "Thanks for your feedback! Your preferences have been updated.",
        "courses_title": "Course Catalog",
        "courses_subtitle": "Browse courses from Coursera and Udemy.",
        "courses_filter_all": "All Categories",
        "courses_filter_platform": "All Platforms",
        "courses_no_results": "No courses found. Try refreshing.",
        "dashboard_welcome": "Welcome back",
        "dashboard_weights": "Your Interest Profile",
        "dashboard_recent": "Recent Activity",
        "dashboard_badges": "Achievements",
        "badge_first_login": "First Steps",
        "badge_first_login_desc": "Created your profile",
        "badge_pre_test": "Challenger",
        "badge_pre_test_desc": "Completed pre-test",
        "badge_post_test": "Scholar",
        "badge_post_test_desc": "Completed post-test",
        "badge_first_rate": "Critic",
        "badge_first_rate_desc": "Rated your first course",
        "badge_improved": "Rising Star",
        "badge_improved_desc": "Improved your score",
        "step_profile": "Profile",
        "step_pretest": "Pre-Test",
        "step_explore": "Explore",
        "step_posttest": "Post-Test",
        "footer_text": "LearnPath AI — Intelligent Course Recommendations",
        "search_placeholder": "Search courses...",
        "no_user": "Please create your profile first.",
        "flash_profile_created": "Profile created successfully! Welcome aboard!",
        "flash_profile_exists": "Profile already exists for this email. Logged in!",
        "flash_test_saved": "Test submitted successfully!",
        "flash_feedback_saved": "Feedback recorded! Recommendations updated.",
        "flash_scrape_done": "Course catalog refreshed!",
        "rating_label": "How would you rate this course?",
        "level_label": "Level",
        "platform_label": "Platform",
        "reviews_label": "reviews",
        "price_label": "Price",
        "view_course": "View Course",
        "rate_course": "Rate Course",
        "sbert_available": "SBERT engine active",
        "sbert_unavailable": "Running without SBERT",
    },
    "ar": {
        "app_name": "مسار التعلّم الذكي",
        "app_tagline": "دليلك الذكي للدورات التعليمية",
        "nav_home": "الرئيسية",
        "nav_onboard": "ابدأ الآن",
        "nav_courses": "الدورات",
        "nav_recommend": "مقترح لك",
        "nav_search": "بحث ذكي",
        "nav_test": "التقييم",
        "nav_benefit": "التقدم",
        "nav_lang": "English",
        "hero_title": "اكتشف مسارك",
        "hero_title_highlight": "التعليمي المثالي",
        "hero_subtitle": "توصيات دورات مدعومة بالذكاء الاصطناعي ومصممة خصيصاً لأهدافك ومستواك واهتماماتك. ابدأ رحلتك اليوم.",
        "hero_cta": "ابدأ رحلتك",
        "hero_explore": "استكشف الدورات",
        "search_title": "البحث الذكي عن الدورات",
        "search_subtitle": "استخدم محرك SBERT الدلالي للعثور على الدورات التي تتطابق مع احتياجاتك.",
        "search_placeholder_ai": "مثال: أريد تعلم بايثون لعلم البيانات...",
        "search_results_for": "نتائج البحث عن",
        "search_no_results": "لم يتم العثور على دورات مطابقة. جرب استعلاماً مختلفاً.",
        "search_match": "تطابق",
        "search_sbert_badge": "بحث دلالي SBERT",
        "search_unavailable": "البحث الدلالي غير متاح. يرجى استخدام كتالوج الدورات.",
        "stats_courses": "دورة متاحة",
        "stats_categories": "تصنيفات",
        "stats_platforms": "منصات",
        "stats_users": "متعلم نشط",
        "onboard_title": "أنشئ ملفك الشخصي",
        "onboard_subtitle": "أخبرنا عن نفسك لنخصص تجربة التعلم لك.",
        "field_name": "الاسم الكامل",
        "field_email": "البريد الإلكتروني",
        "field_level": "المستوى الدراسي",
        "field_goals": "أهداف التعلم",
        "field_name_placeholder": "أدخل اسمك الكامل",
        "field_email_placeholder": "بريدك@مثال.كوم",
        "level_beginner": "مبتدئ",
        "level_intermediate": "متوسط",
        "level_advanced": "متقدم",
        "btn_submit": "إنشاء الملف",
        "btn_continue": "متابعة",
        "btn_back": "رجوع",
        "btn_retake": "إعادة الاختبار",
        "btn_start_test": "بدء التقييم",
        "btn_view_results": "عرض النتائج",
        "btn_rate": "أرسل التقييم",
        "btn_scrape": "تحديث الدورات",
        "test_title": "تقييم المعرفة",
        "test_subtitle_pre": "تقييم ما قبل الدورة — دعنا نرى مستواك الحالي.",
        "test_subtitle_post": "تقييم ما بعد الدورة — دعنا نقيس تطورك.",
        "test_question": "السؤال",
        "test_of": "من",
        "test_submit": "إرسال الإجابات",
        "result_title": "نتائج التقييم",
        "result_score": "درجتك",
        "result_correct": "إجابات صحيحة",
        "result_total": "إجمالي الأسئلة",
        "result_pre_done": "تم إكمال الاختبار القبلي! استكشف الدورات وعد للاختبار البعدي.",
        "result_post_done": "تم إكمال الاختبار البعدي! تحقق من لوحة التقدم.",
        "benefit_title": "تقدم التعلم",
        "benefit_subtitle": "تتبع نموك من خلال مقارنة التقييم القبلي والبعدي.",
        "benefit_pre": "درجة الاختبار القبلي",
        "benefit_post": "درجة الاختبار البعدي",
        "benefit_delta": "التحسن",
        "benefit_no_tests": "أكمل كلا الاختبارين القبلي والبعدي لرؤية تقدمك.",
        "recommend_title": "مقترح لك",
        "recommend_subtitle": "دورات مصممة حسب اهتماماتك وأوزان التعلم الخاصة بك.",
        "recommend_empty": "أكمل ملفك الشخصي أولاً للحصول على توصيات مخصصة.",
        "recommend_based_on": "بناءً على اهتمامك بـ",
        "feedback_title": "قيّم هذه الدورة",
        "feedback_subtitle": "ملاحظاتك تساعدنا في تحسين التوصيات.",
        "feedback_thanks": "شكراً لملاحظاتك! تم تحديث تفضيلاتك.",
        "courses_title": "كتالوج الدورات",
        "courses_subtitle": "تصفح الدورات من كورسيرا ويوديمي.",
        "courses_filter_all": "جميع التصنيفات",
        "courses_filter_platform": "جميع المنصات",
        "courses_no_results": "لم يتم العثور على دورات. حاول التحديث.",
        "dashboard_welcome": "مرحباً بعودتك",
        "dashboard_weights": "ملف اهتماماتك",
        "dashboard_recent": "النشاط الأخير",
        "dashboard_badges": "الإنجازات",
        "badge_first_login": "الخطوات الأولى",
        "badge_first_login_desc": "أنشأت ملفك الشخصي",
        "badge_pre_test": "المتحدي",
        "badge_pre_test_desc": "أكملت الاختبار القبلي",
        "badge_post_test": "العالم",
        "badge_post_test_desc": "أكملت الاختبار البعدي",
        "badge_first_rate": "الناقد",
        "badge_first_rate_desc": "قيّمت أول دورة",
        "badge_improved": "النجم الصاعد",
        "badge_improved_desc": "حسّنت درجتك",
        "step_profile": "الملف الشخصي",
        "step_pretest": "اختبار قبلي",
        "step_explore": "استكشاف",
        "step_posttest": "اختبار بعدي",
        "footer_text": "مسار التعلّم الذكي — توصيات دورات ذكية",
        "search_placeholder": "ابحث عن دورات...",
        "no_user": "يرجى إنشاء ملفك الشخصي أولاً.",
        "flash_profile_created": "تم إنشاء الملف الشخصي بنجاح! أهلاً بك!",
        "flash_profile_exists": "الملف الشخصي موجود بالفعل. تم تسجيل الدخول!",
        "flash_test_saved": "تم إرسال الاختبار بنجاح!",
        "flash_feedback_saved": "تم تسجيل الملاحظات! تم تحديث التوصيات.",
        "flash_scrape_done": "تم تحديث كتالوج الدورات!",
        "rating_label": "كيف تقيّم هذه الدورة؟",
        "level_label": "المستوى",
        "platform_label": "المنصة",
        "reviews_label": "مراجعة",
        "price_label": "السعر",
        "view_course": "عرض الدورة",
        "rate_course": "قيّم الدورة",
        "sbert_available": "محرك SBERT مُفعّل",
        "sbert_unavailable": "يعمل بدون SBERT",
    },
}

# ══════════════════════════════════════════════════════════════════
# DATABASE HELPERS
# ══════════════════════════════════════════════════════════════════
def load_db() -> dict:
    """Load the JSON database."""
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"users": []}


def save_db(db: dict):
    """Save the JSON database."""
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(db, f, indent=2, ensure_ascii=False)


def get_user(email: str) -> dict | None:
    """Find a user by email."""
    db = load_db()
    for user in db["users"]:
        if user["email"] == email:
            return user
    return None


def get_current_user() -> dict | None:
    """Get the currently logged-in user from session."""
    email = session.get("user_email")
    if email:
        return get_user(email)
    return None


def update_user(email: str, updates: dict):
    """Update a user's data."""
    db = load_db()
    for i, user in enumerate(db["users"]):
        if user["email"] == email:
            db["users"][i].update(updates)
            save_db(db)
            return
    raise ValueError(f"User {email} not found")


def require_user(f):
    """Decorator that ensures a user is logged in."""
    @wraps(f)
    def decorated(*args, **kwargs):
        user = get_current_user()
        if not user:
            flash(t("no_user"), "warning")
            return redirect(url_for("onboard"))
        return f(*args, **kwargs)
    return decorated


# ══════════════════════════════════════════════════════════════════
# TRANSLATION HELPERS
# ══════════════════════════════════════════════════════════════════
def get_lang() -> str:
    """Get current language from session."""
    return session.get("lang", "en")


def t(key: str) -> str:
    """Translate a key to the current language."""
    lang = get_lang()
    return TRANSLATIONS.get(lang, TRANSLATIONS["en"]).get(key, key)


def get_cat_display(cat: str) -> str:
    """Get category display name in current language."""
    lang = get_lang()
    return CATEGORY_DISPLAY.get(lang, CATEGORY_DISPLAY["en"]).get(cat, cat)


@app.context_processor
def inject_globals():
    """Inject translation function and helpers into all templates."""
    lang = get_lang()
    user = get_current_user()
    courses = load_courses_cache()
    return {
        "t": t,
        "lang": lang,
        "dir": "rtl" if lang == "ar" else "ltr",
        "current_user": user,
        "categories": CATEGORIES,
        "category_icons": CATEGORY_ICONS,
        "get_cat_display": get_cat_display,
        "total_courses": len(courses),
        "sbert_available": sbert_engine is not None,
    }


# ══════════════════════════════════════════════════════════════════
# AI QUESTION GENERATOR (Ollama → Category Fallback)
# ══════════════════════════════════════════════════════════════════
import re
import random

OLLAMA_URL = "http://127.0.0.1:11434/api/generate"  # Using 127.0.0.1 (better on Windows)
OLLAMA_MODEL = "llama3.2"

def load_category_questions():
    """Load pre-defined questions by category from JSON."""
    try:
        path = os.path.join(os.path.dirname(__file__), "category_questions.json")
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        print(f"Error loading category_questions.json: {e}")
    return {}

# Global cache for category questions
CATEGORY_QUESTIONS_BANK = load_category_questions()

# Generic ultimate fallback (used only if category-specific bank is empty)
ULTIMATE_FALLBACK_QUESTIONS = [
    {
        "q": "What is the primary purpose of taking a structured course?",
        "options": ["To build practical, applicable skills", "To memorize facts for one day", "To bypass difficult topics", "To collect certificates only"],
        "answer": 0,
    },
    {
        "q": "Which study method is most effective for long-term retention?",
        "options": ["Cramming all night", "Spaced repetition and active recall", "Reading only once", "Watching videos on mute"],
        "answer": 1,
    }
]


def generate_questions_with_groq(course_title: str, category: str, description: str, level: str, num_questions: int = 5) -> list:
    """
    Generate course-specific questions using Groq API.
    Falls back to category-aware questions if Groq is unavailable.
    """
    import os
    import re
    import json
    import random
    from dotenv import load_dotenv

    load_dotenv()
    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        print("⚠️ Groq API key not found in .env")
    else:
        try:
            from groq import Groq
            client = Groq(api_key=api_key)

            prompt = f"""You are an educational assessment expert. Generate exactly {num_questions} multiple-choice questions to assess a student's knowledge about the following course:

Title: {course_title}
Category: {category}
Level: {level}
Course Description:
{description}

Each question must comprehensively test the real understanding of the subject taking into account the course level and description.

Return ONLY a JSON array in this exact format, no other text or explanation:
[
  {{
    "q": "Question text here?",
    "options": ["Option A", "Option B", "Option C", "Option D"],
    "answer": 0
  }}
]

The "answer" field is the 0-based index of the correct option. Generate exactly {num_questions} questions."""

            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": "You are a specialized AI that only outputs strict JSON arrays formatting multiple-choice questions."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
            )
            raw = response.choices[0].message.content
            
            # Extract JSON array from response
            match = re.search(r'\[.*\]', raw, re.DOTALL)
            if match:
                questions = json.loads(match.group())
                # Validate structure
                valid = []
                for q in questions:
                    if (isinstance(q, dict) and "q" in q and "options" in q and "answer" in q
                            and isinstance(q["options"], list) and len(q["options"]) >= 2
                            and isinstance(q["answer"], int)):
                        valid.append(q)
                if len(valid) >= 1:
                    print(f"✅ Groq generated {len(valid)} questions for: {course_title}")
                    return valid[:num_questions]
        except Exception as e:
            print(f"⚠️  Groq unavailable or errored: {e}")

    # Fallback: use category-specific questions
    print(f"📝 Using category-specific fallback for: {category} ({course_title})")
    cat_questions = CATEGORY_QUESTIONS_BANK.get(category, [])
    if not cat_questions:
        # If specific category not found, try generic categories or ultimate fallback
        cat_questions = ULTIMATE_FALLBACK_QUESTIONS
        
    # Return a random sample if we have more than needed, otherwise return all
    if len(cat_questions) > num_questions:
        return random.sample(cat_questions, num_questions)
    return cat_questions


def get_or_generate_questions(enrollment: dict) -> list:
    """
    Get cached questions for this enrollment, or generate new ones using Groq.
    """
    if enrollment.get("questions"):
        return enrollment["questions"]

    course_title = enrollment.get("course_title", "General Course")
    category = enrollment.get("category", "programming")
    course_id = enrollment.get("course_id")
    level = enrollment.get("level", "Beginner")
    
    courses = load_courses_cache()
    if courses:
        course = next((c for c in courses if c.get("id") == course_id), {})
        description = course.get("description", "No description available.")
    else:
        description = "No description available."

    return generate_questions_with_groq(course_title, category, description, level)


# ══════════════════════════════════════════════════════════════════
# ROUTES
# ══════════════════════════════════════════════════════════════════

# ── Language Toggle ───────────────────────────────────────────────
@app.route("/set_lang/<lang>")
def set_lang(lang):
    """Toggle between English and Arabic."""
    if lang in ("en", "ar"):
        session["lang"] = lang
    return redirect(request.referrer or url_for("index"))


# ── Landing Page / Dashboard ─────────────────────────────────────
@app.route("/")
def index():
    """Landing page — if user logged in, show dashboard; else show hero."""
    user = get_current_user()
    courses = load_courses_cache()

    # Count stats
    platforms = set(c.get("platform", "") for c in courses)

    badges = []
    if user:
        enrolled = user.get("enrolled_courses", [])
        has_pre = any(e.get("pre_score") is not None for e in enrolled)
        has_post = any(e.get("post_score") is not None for e in enrolled)
        has_improvement = any(
            e.get("pre_score") is not None and e.get("post_score") is not None and e["post_score"] > e["pre_score"]
            for e in enrolled
        )
        badges.append({"key": "first_login", "icon": "fa-user-check", "earned": True})
        badges.append({"key": "pre_test", "icon": "fa-clipboard-check", "earned": has_pre})
        badges.append({"key": "post_test", "icon": "fa-graduation-cap", "earned": has_post})
        badges.append({"key": "first_rate", "icon": "fa-star", "earned": len(user.get("feedback_history", [])) > 0})
        badges.append({"key": "improved", "icon": "fa-arrow-trend-up", "earned": has_improvement})

    return render_template(
        "index.html",
        user=user,
        stats={
            "courses": len(courses),
            "categories": len(CATEGORIES),
            "platforms": len(platforms),
        },
        badges=badges,
    )


# ── Onboarding ───────────────────────────────────────────────────
@app.route("/onboard", methods=["GET", "POST"])
def onboard():
    """User registration / onboarding form."""
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        level = request.form.get("level", "Beginner")
        goals = request.form.getlist("goals")

        if not name or not email or not goals:
            flash("Please fill in all required fields.", "error")
            return redirect(url_for("onboard"))

        db = load_db()
        existing = get_user(email)

        if existing:
            session["user_email"] = email
            flash(t("flash_profile_exists"), "info")
            return redirect(url_for("index"))

        # Create new user — weights start at 0, grow only from course completions
        user = {
            "id": str(uuid.uuid4()),
            "name": name,
            "email": email,
            "level": level,
            "goals": goals,
            "weights": {cat: 0.0 for cat in CATEGORIES},
            "tests": {"pre": None, "post": None},
            "enrolled_courses": [],
            "active_course": None,
            "feedback_history": [],
            "created_at": datetime.now().isoformat(),
        }
        db["users"].append(user)
        save_db(db)

        session["user_email"] = email
        flash(t("flash_profile_created"), "success")
        return redirect(url_for("index"))

    return render_template("onboarding.html")


# ══════════════════════════════════════════════════════════════════
# STUDY PLAN GENERATOR
# ══════════════════════════════════════════════════════════════════
STUDY_PLAN_TEMPLATES = [
    {"title": "Introduction & Course Overview", "desc": "Review the syllabus, objectives, and set up your environment."},
    {"title": "Core Concepts — Part 1", "desc": "Study the foundational theory and key terminology."},
    {"title": "Core Concepts — Part 2", "desc": "Deepen your understanding of the main principles."},
    {"title": "Hands-On Practice 1", "desc": "Complete the first set of exercises or labs."},
    {"title": "Mid-Course Review", "desc": "Review notes, revisit tricky topics, and consolidate learning."},
    {"title": "Advanced Topics — Part 1", "desc": "Explore more complex concepts and real-world applications."},
    {"title": "Advanced Topics — Part 2", "desc": "Go deeper into specialised areas of the course."},
    {"title": "Hands-On Practice 2", "desc": "Complete the second set of exercises or a mini-project."},
    {"title": "Case Study / Real-World Application", "desc": "Study real use cases and apply your knowledge."},
    {"title": "Final Review & Summary", "desc": "Revise all topics, review notes, and prepare for assessment."},
]

SCHEDULE_CONFIGS = {
    "weekdays":  {"days_per_week": 5, "label": "Weekdays Only (Mon–Fri)"},
    "weekends":  {"days_per_week": 2, "label": "Weekends Only (Sat–Sun)"},
    "daily":     {"days_per_week": 7, "label": "Every Day"},
    "flexible":  {"days_per_week": 3, "label": "Flexible (3 days/week)"},
}


def generate_study_plan(schedule_type: str, course_title: str) -> list:
    """Generate a study plan with calendar dates based on schedule type."""
    config = SCHEDULE_CONFIGS.get(schedule_type, SCHEDULE_CONFIGS["flexible"])
    items = []
    today = datetime.now().date()
    day_cursor = today
    
    # Map schedule types to actual weekday sets
    if schedule_type == "weekdays":
        valid_days = {0, 1, 2, 3, 4}  # Mon-Fri
    elif schedule_type == "weekends":
        valid_days = {5, 6}  # Sat-Sun
    elif schedule_type == "daily":
        valid_days = {0, 1, 2, 3, 4, 5, 6}
    else:  # flexible — Mon, Wed, Fri
        valid_days = {0, 2, 4}

    for i, template in enumerate(STUDY_PLAN_TEMPLATES):
        # Find the next valid day
        while day_cursor.weekday() not in valid_days:
            day_cursor += timedelta(days=1)
        items.append({
            "id": str(uuid.uuid4())[:8],
            "index": i,
            "title": template["title"],
            "desc": template["desc"],
            "date": day_cursor.isoformat(),
            "checked": False,
            "checked_at": None,
        })
        day_cursor += timedelta(days=1)
    return items


def get_enrollment(user: dict, enrollment_id: str) -> dict | None:
    """Find an enrollment by its ID."""
    for enr in user.get("enrolled_courses", []):
        if enr.get("id") == enrollment_id:
            return enr
    return None


# ══════════════════════════════════════════════════════════════════
# COURSE-DRIVEN ROUTES
# ══════════════════════════════════════════════════════════════════

# ── Course Detail Page ────────────────────────────────────────────
@app.route("/course/<course_id>")
def course_detail(course_id):
    """Full detail page for a single course with Enroll CTA."""
    courses = load_courses_cache()
    course = next((c for c in courses if c.get("id") == course_id), None)
    if not course:
        flash("Course not found.", "error")
        return redirect(url_for("courses_page"))

    user = get_current_user()
    existing_enrollment = None
    if user:
        for enr in user.get("enrolled_courses", []):
            if enr.get("course_id") == course_id:
                existing_enrollment = enr
                break

    return render_template(
        "course_detail.html",
        course=course,
        enrollment=existing_enrollment,
    )


# ── Enroll ────────────────────────────────────────────────────────
@app.route("/enroll/<course_id>", methods=["GET", "POST"])
@require_user
def enroll(course_id):
    """Enroll in a course: pick schedule, generate study plan, go to pre-test."""
    courses = load_courses_cache()
    course = next((c for c in courses if c.get("id") == course_id), None)
    if not course:
        flash("Course not found.", "error")
        return redirect(url_for("courses_page"))

    user = get_current_user()
    # Check if already enrolled
    for enr in user.get("enrolled_courses", []):
        if enr.get("course_id") == course_id:
            flash("You are already enrolled in this course!", "info")
            return redirect(url_for("plan", enrollment_id=enr["id"]))

    if request.method == "POST":
        schedule_type = request.form.get("schedule", "flexible")
        study_plan = generate_study_plan(schedule_type, course.get("title", ""))

        enrollment = {
            "id": str(uuid.uuid4())[:12],
            "course_id": course_id,
            "course_title": course.get("title", "Unknown"),
            "category": course.get("category", "programming"),
            "platform": course.get("platform", ""),
            "url": course.get("url", ""),
            "level": course.get("level", "Beginner"),
            "enrolled_at": datetime.now().isoformat(),
            "schedule_type": schedule_type,
            "pre_score": None,
            "post_score": None,
            "study_plan": study_plan,
            "completed": False,
            "completed_at": None,
        }

        enrolled = user.get("enrolled_courses", [])
        enrolled.append(enrollment)
        update_user(user["email"], {"enrolled_courses": enrolled, "active_course": enrollment["id"]})

        flash(f"Enrolled in {course['title']}! Take the pre-assessment now.", "success")
        return redirect(url_for("test", test_type="pre", enrollment_id=enrollment["id"]))

    return render_template("enroll.html", course=course, schedules=SCHEDULE_CONFIGS)


# ── Testing System (tied to enrollment) ───────────────────────────
@app.route("/test/<test_type>/<enrollment_id>")
@require_user
def test(test_type, enrollment_id):
    """Serve the pre or post test for a specific enrollment."""
    if test_type not in ("pre", "post"):
        return redirect(url_for("index"))

    user = get_current_user()
    enrollment = get_enrollment(user, enrollment_id)
    if not enrollment:
        flash("Enrollment not found.", "error")
        return redirect(url_for("index"))

    # Post-test: check ALL items are completed
    if test_type == "post":
        plan = enrollment.get("study_plan", [])
        all_done = all(item.get("checked", False) for item in plan)
        if not all_done:
            flash("Complete all study plan items before taking the post-assessment.", "warning")
            return redirect(url_for("plan", enrollment_id=enrollment_id))

    # Generate/load course-specific questions and cache them
    questions = get_or_generate_questions(enrollment)
    if not enrollment.get("questions"):
        # Cache into enrollment so scoring works
        enrolled = user.get("enrolled_courses", [])
        for enr in enrolled:
            if enr.get("id") == enrollment_id:
                enr["questions"] = questions
                break
        update_user(user["email"], {"enrolled_courses": enrolled})

    return render_template(
        "test.html",
        test_type=test_type,
        questions=questions,
        enrollment=enrollment,
    )


@app.route("/submit_test", methods=["POST"])
@require_user
def submit_test():
    """Calculate and save test score for a specific enrollment."""
    test_type = request.form.get("test_type", "pre")
    enrollment_id = request.form.get("enrollment_id", "")

    user = get_current_user()
    enrollment = get_enrollment(user, enrollment_id)
    if not enrollment:
        flash("Enrollment not found.", "error")
        return redirect(url_for("index"))

    # Use cached course-specific questions, or ultimate fallback
    questions = enrollment.get("questions") or ULTIMATE_FALLBACK_QUESTIONS

    correct = 0
    total = len(questions)
    user_answers = []

    for i, q in enumerate(questions):
        answer = request.form.get(f"q{i}")
        is_correct = answer is not None and int(answer) == q["answer"]
        if is_correct:
            correct += 1
        user_answers.append({
            "question": q["q"],
            "selected": int(answer) if answer is not None else -1,
            "correct": q["answer"],
            "correct_text": q["options"][q["answer"]] if q["options"] else "",
            "selected_text": q["options"][int(answer)] if answer is not None and int(answer) < len(q["options"]) else "Not answered",
            "is_correct": is_correct,
        })

    score = round((correct / total) * 100) if total > 0 else 0

    # Save score to enrollment
    enrolled = user.get("enrolled_courses", [])
    for enr in enrolled:
        if enr.get("id") == enrollment_id:
            if test_type == "pre":
                enr["pre_score"] = score
            else:
                enr["post_score"] = score
                # Mark course as completed
                enr["completed"] = True
                enr["completed_at"] = datetime.now().isoformat()
                # RL weight reward on completion
                weights = user.get("weights", {})
                cat = enr.get("category", "programming")
                weights[cat] = min(1.0, weights.get(cat, 0.0) + 0.15)
                if enr.get("pre_score") is not None and score > enr["pre_score"]:
                    weights[cat] = min(1.0, weights[cat] + 0.1)  # Improvement bonus
                update_user(user["email"], {"weights": weights})
            break
    update_user(user["email"], {"enrolled_courses": enrolled})

    flash(t("flash_test_saved"), "success")

    return render_template(
        "test_result.html",
        test_type=test_type,
        score=score,
        correct=correct,
        total=total,
        answers=user_answers,
        enrollment_id=enrollment_id,
    )


# ── Study Plan ────────────────────────────────────────────────────
@app.route("/plan/<enrollment_id>")
@require_user
def plan(enrollment_id):
    """Show the study plan checklist and calendar for an enrolled course."""
    user = get_current_user()
    enrollment = get_enrollment(user, enrollment_id)
    if not enrollment:
        flash("Enrollment not found.", "error")
        return redirect(url_for("index"))

    study_plan = enrollment.get("study_plan", [])
    total = len(study_plan)
    checked = sum(1 for item in study_plan if item.get("checked", False))
    progress = round((checked / total) * 100) if total > 0 else 0
    all_done = checked == total

    # Build calendar data (4 weeks from enrollment)
    try:
        enroll_date = datetime.fromisoformat(enrollment["enrolled_at"]).date()
    except Exception:
        enroll_date = datetime.now().date()
    
    plan_dates = {item["date"] for item in study_plan}
    checked_dates = {item["date"] for item in study_plan if item.get("checked")}

    # Generate 5 weeks of calendar starting from Sunday before enroll_date
    cal_start = enroll_date - timedelta(days=enroll_date.weekday())  # Monday
    cal_start -= timedelta(days=1)  # Sunday
    calendar_weeks = []
    for week in range(5):
        days = []
        for d in range(7):
            day = cal_start + timedelta(days=week * 7 + d)
            days.append({
                "date": day.isoformat(),
                "day": day.day,
                "is_plan": day.isoformat() in plan_dates,
                "is_checked": day.isoformat() in checked_dates,
                "is_today": day == datetime.now().date(),
                "is_past": day < datetime.now().date(),
            })
        calendar_weeks.append(days)

    return render_template(
        "plan.html",
        enrollment=enrollment,
        study_plan=study_plan,
        progress=progress,
        total=total,
        checked=checked,
        all_done=all_done,
        calendar_weeks=calendar_weeks,
    )


# ── Check Item API ────────────────────────────────────────────────
@app.route("/api/check_item", methods=["POST"])
@require_user
def check_item():
    """Toggle a checklist item on/off via AJAX."""
    data = request.get_json()
    enrollment_id = data.get("enrollment_id", "")
    item_id = data.get("item_id", "")

    user = get_current_user()
    enrolled = user.get("enrolled_courses", [])
    for enr in enrolled:
        if enr.get("id") == enrollment_id:
            for item in enr.get("study_plan", []):
                if item.get("id") == item_id:
                    item["checked"] = not item.get("checked", False)
                    item["checked_at"] = datetime.now().isoformat() if item["checked"] else None
                    break
            # Calculate progress
            plan = enr.get("study_plan", [])
            total = len(plan)
            checked = sum(1 for i in plan if i.get("checked"))
            update_user(user["email"], {"enrolled_courses": enrolled})
            return jsonify({"ok": True, "checked": item["checked"], "progress": round((checked / total) * 100) if total else 0, "all_done": checked == total})

    return jsonify({"ok": False}), 404


# ── Benefit Dashboard (per-course) ────────────────────────────────
@app.route("/benefit")
@require_user
def benefit():
    """Show per-course pre vs post test comparison."""
    user = get_current_user()
    enrolled = user.get("enrolled_courses", [])

    # Build per-course comparison data
    course_progress = []
    for enr in enrolled:
        pre = enr.get("pre_score")
        post = enr.get("post_score")
        delta = (post - pre) if pre is not None and post is not None else None
        plan = enr.get("study_plan", [])
        total = len(plan)
        checked = sum(1 for i in plan if i.get("checked"))
        course_progress.append({
            "id": enr.get("id"),
            "title": enr.get("course_title", "Unknown"),
            "category": enr.get("category", ""),
            "platform": enr.get("platform", ""),
            "pre_score": pre,
            "post_score": post,
            "delta": delta,
            "plan_progress": round((checked / total) * 100) if total else 0,
            "completed": enr.get("completed", False),
        })

    return render_template("benefit.html", course_progress=course_progress)


# ── Recommendation Engine (RL-enhanced) ──────────────────────────
@app.route("/recommend")
@require_user
def recommend():
    """Suggest courses based on RL weights, optionally enhanced by SBERT."""
    user = get_current_user()
    weights = user.get("weights", {})
    user_level = user.get("level", "Beginner")
    user_goals = user.get("goals", [])
    courses = load_courses_cache()

    # Exclude already enrolled courses
    enrolled_ids = {e.get("course_id") for e in user.get("enrolled_courses", [])}
    courses = [c for c in courses if c.get("id") not in enrolled_ids]

    if not courses:
        return render_template("recommend.html", recommendations=[], top_category="", sbert_used=False)

    sbert_scores = {}
    sbert_used = False
    if sbert_engine and user_goals:
        try:
            goal_query = " ".join([get_cat_display(g) for g in user_goals])
            sbert_results = sbert_engine.recommend(goal_query, user_level, top_n=50)
            if not sbert_results.empty:
                for _, row in sbert_results.iterrows():
                    title = row.get("course_title", "")
                    sbert_scores[title.lower()] = float(row.get("score", 0))
                sbert_used = True
        except Exception as e:
            print(f"⚠️  SBERT recommendation error: {e}")

    scored = []
    for course in courses:
        cat = course.get("category", "programming")
        cat_weight = weights.get(cat, 0.0)
        level_bonus = 1.2 if course.get("level", "") == user_level else 1.0
        rating_bonus = (course.get("rating", 3.0) / 5.0)
        # For users with all-zero weights, use goal-based scoring
        goal_bonus = 1.5 if cat in user_goals else 1.0
        sbert_boost = 1.0
        if sbert_scores:
            title_key = course.get("title", "").lower()
            for sbert_title, sbert_score in sbert_scores.items():
                if sbert_title in title_key or title_key in sbert_title:
                    sbert_boost = 1.0 + sbert_score
                    break
        base = max(cat_weight, 0.1)  # Minimum base so zero-weight courses still score
        score = base * level_bonus * rating_bonus * goal_bonus * sbert_boost
        scored.append({**course, "rec_score": round(score, 3), "sbert_boosted": sbert_boost > 1.0})

    scored.sort(key=lambda x: x["rec_score"], reverse=True)
    top_courses = scored[:12]
    top_cat = max(weights, key=weights.get) if weights and any(v > 0 for v in weights.values()) else (user_goals[0] if user_goals else "")

    return render_template("recommend.html", recommendations=top_courses, top_category=top_cat, sbert_used=sbert_used)


# ── SBERT Semantic Search ─────────────────────────────────────────
@app.route("/search", methods=["GET", "POST"])
def search():
    """AI-powered semantic search using SBERT."""
    recommendations = []
    search_query = ""
    selected_level = "All Levels"

    if not sbert_engine:
        flash(t("search_unavailable"), "warning")
        return render_template("search.html", recommendations=[], search_query="", selected_level="All Levels")

    if request.method == "POST":
        search_query = request.form.get("search_query", "").strip()
        selected_level = request.form.get("level", "All Levels")
        if search_query:
            try:
                results = sbert_engine.recommend(search_query, selected_level, top_n=50)
                if not results.empty:
                    recommendations = results.to_dict(orient="records")
                    user = get_current_user()
                    if user:
                        weights = user.get("weights", {})
                        for rec in recommendations:
                            from scraper import classify_category
                            cat = classify_category(rec.get("course_title", ""), rec.get("subject", ""))
                            rl_boost = weights.get(cat, 0.0)
                            rec["rl_boost"] = round(rl_boost, 2)
                            rec["combined_score"] = round(rec.get("score", 0) * (0.7 + rl_boost * 0.3), 3)
                        recommendations.sort(key=lambda x: x.get("combined_score", 0), reverse=True)
            except Exception as e:
                print(f"❌ Search error: {e}")
                flash(f"Search error: {e}", "error")

    return render_template("search.html", recommendations=recommendations, search_query=search_query, selected_level=selected_level)


# ── Feedback / Rating ────────────────────────────────────────────
@app.route("/feedback", methods=["GET", "POST"])
@require_user
def feedback():
    """Handle course rating feedback with RL weight adjustment."""
    if request.method == "POST":
        course_id = request.form.get("course_id", "")
        course_title = request.form.get("course_title", "")
        course_category = request.form.get("course_category", "programming")
        rating = int(request.form.get("rating", 3))
        user = get_current_user()
        weights = user.get("weights", {})
        adjustment = {5: 0.1, 4: 0.05, 3: 0, 2: -0.05, 1: -0.1}.get(rating, 0)
        if course_category in weights:
            weights[course_category] = max(0.0, min(1.0, weights[course_category] + adjustment))
        history = user.get("feedback_history", [])
        history.append({"course_id": course_id, "course_title": course_title, "category": course_category, "rating": rating, "adjustment": adjustment, "timestamp": datetime.now().isoformat()})
        update_user(user["email"], {"weights": weights, "feedback_history": history})
        flash(t("flash_feedback_saved"), "success")
        return redirect(url_for("recommend"))

    course_id = request.args.get("course_id", "")
    courses = load_courses_cache()
    course = next((c for c in courses if c.get("id") == course_id), None)
    if not course:
        return redirect(url_for("courses_page"))
    return render_template("feedback.html", course=course)


# ── Courses Catalog ───────────────────────────────────────────────
@app.route("/courses")
def courses_page():
    """Browse all scraped courses with filters."""
    courses = load_courses_cache()
    category_filter = request.args.get("category", "")
    platform_filter = request.args.get("platform", "")
    search_query = request.args.get("q", "").lower()
    if category_filter:
        courses = [c for c in courses if c.get("category") == category_filter]
    if platform_filter:
        courses = [c for c in courses if c.get("platform") == platform_filter]
    if search_query:
        courses = [c for c in courses if search_query in c.get("title", "").lower()]
    all_courses = load_courses_cache()
    platforms = sorted(set(c.get("platform", "") for c in all_courses))
    return render_template("courses.html", courses=courses, platforms=platforms, current_category=category_filter, current_platform=platform_filter, search_query=search_query)


# ── Manual Scraper Trigger ────────────────────────────────────────
@app.route("/scrape", methods=["POST"])
def scrape():
    run_scraper()
    flash(t("flash_scrape_done"), "success")
    return redirect(url_for("courses_page"))


# ── API endpoints ─────────────────────────────────────────────────
@app.route("/api/weights")
@require_user
def api_weights():
    """Return user weights as JSON for the radar chart."""
    user = get_current_user()
    lang = get_lang()
    weights = user.get("weights", {})
    labels = [get_cat_display(cat) for cat in CATEGORIES]
    values = [weights.get(cat, 0.0) for cat in CATEGORIES]
    return jsonify({"labels": labels, "values": values})


# ══════════════════════════════════════════════════════════════════
# STARTUP
# ══════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    start_scraper_thread(interval_hours=6)
    if not os.path.exists(DB_FILE):
        save_db({"users": []})
    print("\n🚀 LearnPath AI is running at http://127.0.0.1:5000\n")
    app.run(debug=True, port=5000, use_reloader=False)

