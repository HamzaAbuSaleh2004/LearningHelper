"""
Custom tools for the LearnPath Mentor Agent.
These tools give the agent access to the local course database and user data.
"""

import json
import os
import csv

# Resolve paths relative to this file
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_FILE = os.path.join(BASE_DIR, "course_rec", "db.json")
COURSES_CACHE = os.path.join(BASE_DIR, "course_rec", "courses_cache.json")
CLEANED_CSV = os.path.join(BASE_DIR, "data", "processed", "cleaned_courses.csv")


def get_user_profile(email: str) -> str:
    """
    Retrieve the learner's profile including their skill level, learning goals,
    and interest weights. Use this to personalize advice and recommendations.

    Args:
        email: The learner's email address.

    Returns:
        A formatted string with the learner's profile information.
    """
    try:
        if not os.path.exists(DB_FILE):
            return "No user database found."
        with open(DB_FILE, "r", encoding="utf-8") as f:
            db = json.load(f)
        user = next((u for u in db.get("users", []) if u.get("email") == email), None)
        if not user:
            return f"No profile found for {email}."

        goals = ", ".join(user.get("goals", [])) or "not specified"
        level = user.get("level", "not specified")
        weights = user.get("weights", {})
        top_interests = sorted(weights.items(), key=lambda x: x[1], reverse=True)[:3]
        interests_str = ", ".join(
            f"{cat.replace('_', ' ')} ({round(v * 100)}%)" for cat, v in top_interests if v > 0
        ) or "no interest data yet"

        enrolled = user.get("enrolled_courses", [])
        active = [c for c in enrolled if not c.get("completed")]
        completed = [c for c in enrolled if c.get("completed")]

        lines = [
            f"Learner Profile for {user.get('name', 'Unknown')} ({email}):",
            f"  Level: {level}",
            f"  Learning Goals: {goals}",
            f"  Top Interests: {interests_str}",
            f"  Active Courses: {len(active)} enrolled",
            f"  Completed Courses: {len(completed)}",
        ]
        if active:
            lines.append("  Currently Studying:")
            for c in active[:3]:
                lines.append(f"    - {c.get('course_title', 'Unknown')} ({c.get('platform', '')})")
        return "\n".join(lines)
    except Exception as e:
        return f"Error retrieving profile: {e}"


def get_enrolled_courses(email: str) -> str:
    """
    Get the list of courses a learner is currently enrolled in or has completed.
    Use this to understand their learning history and avoid recommending courses
    they already have.

    Args:
        email: The learner's email address.

    Returns:
        A formatted list of enrolled and completed courses.
    """
    try:
        if not os.path.exists(DB_FILE):
            return "No user database found."
        with open(DB_FILE, "r", encoding="utf-8") as f:
            db = json.load(f)
        user = next((u for u in db.get("users", []) if u.get("email") == email), None)
        if not user:
            return f"No profile found for {email}."

        enrolled = user.get("enrolled_courses", [])
        if not enrolled:
            return "This learner has not enrolled in any courses yet."

        lines = ["Enrolled Courses:"]
        for c in enrolled:
            status = "Completed" if c.get("completed") else "In Progress"
            lines.append(
                f"  [{status}] {c.get('course_title', 'Unknown')} "
                f"on {c.get('platform', 'Unknown')} "
                f"(Category: {c.get('category', 'Unknown')})"
            )
        return "\n".join(lines)
    except Exception as e:
        return f"Error retrieving courses: {e}"


def search_local_courses(query: str, limit: int = 8) -> str:
    """
    Search the local course database for courses matching a query by keyword.
    Use this to find specific courses available on the LearnPath platform
    before making external search recommendations.

    Args:
        query: A search term or topic (e.g., "Python", "AWS certification", "machine learning").
        limit: Maximum number of results to return (default 8).

    Returns:
        A formatted list of matching courses with title, platform, level, and rating.
    """
    try:
        query_lower = query.lower()
        results = []

        # Search in courses_cache.json first
        if os.path.exists(COURSES_CACHE):
            with open(COURSES_CACHE, "r", encoding="utf-8") as f:
                cache = json.load(f)
            for course in cache:
                title = course.get("course_title", "")
                desc = course.get("description", "")
                if query_lower in title.lower() or query_lower in desc.lower():
                    results.append({
                        "title": title,
                        "platform": course.get("platform", "Unknown"),
                        "level": course.get("level", "Unknown"),
                        "rating": course.get("rating", 0),
                        "category": course.get("category", ""),
                    })

        # Also search CSV if we have room
        if len(results) < limit and os.path.exists(CLEANED_CSV):
            with open(CLEANED_CSV, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if len(results) >= limit * 2:
                        break
                    title = row.get("course_title", "")
                    if query_lower in title.lower():
                        results.append({
                            "title": title,
                            "platform": "Udemy",
                            "level": row.get("level", "Unknown"),
                            "rating": row.get("avg_rating", 0),
                            "category": row.get("category", ""),
                        })

        if not results:
            return f"No local courses found matching '{query}'. Consider searching online for the latest options."

        # Sort by rating descending and take top results
        results.sort(key=lambda x: float(x.get("rating") or 0), reverse=True)
        results = results[:limit]

        lines = [f"Local courses matching '{query}':"]
        for r in results:
            rating = f"★ {float(r['rating']):.1f}" if r.get("rating") else "No rating"
            lines.append(
                f"  • {r['title']} | {r['platform']} | {r['level']} | {rating}"
            )
        return "\n".join(lines)
    except Exception as e:
        return f"Error searching courses: {e}"
