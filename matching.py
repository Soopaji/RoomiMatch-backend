# matching.py
import json
from models import db, User, Match

def compatibility_score(user: User, other: User) -> float:
    """
    Calculate compatibility between two users.
    Higher score = better match.
    """

    score = 0

    # Age similarity (closer ages = higher score)
    if user.age and other.age:
        age_diff = abs(user.age - other.age)
        score += max(0, 20 - age_diff)  

    # Same gender preference (optional)
    if user.gender == other.gender:
        score += 10

    # Same occupation
    if user.occupation == other.occupation:
        score += 10

    # Budget closeness
    if user.budget and other.budget:
        try:
            b1 = int(str(user.budget).replace("₹", "").replace("k", "000"))
            b2 = int(str(other.budget).replace("₹", "").replace("k", "000"))
            score += max(0, 20 - abs(b1 - b2) // 1000)
        except:
            pass

    # Habits similarity
    try:
        u_habits = set(json.loads(user.habits))
        o_habits = set(json.loads(other.habits))
        score += len(u_habits.intersection(o_habits)) * 5
    except:
        pass

    # Interests similarity
    try:
        u_interests = set(json.loads(user.interests))
        o_interests = set(json.loads(other.interests))
        score += len(u_interests.intersection(o_interests)) * 4
    except:
        pass

    return score


def find_potential_matches(user_id, filters=None):
    """Returns sorted list of potential matches for a user based on filters."""

    user = User.query.get(user_id)
    if not user:
        return []

    query = User.query.filter(User.id != user_id)

    # Apply filters
    if filters:
        if "gender" in filters:
            query = query.filter_by(gender=filters["gender"])
        if "budget" in filters:
            query = query.filter_by(budget=filters["budget"])
        if "occupation" in filters:
            query = query.filter_by(occupation=filters["occupation"])

    candidates = query.all()

    results = []
    for other in candidates:
        score = compatibility_score(user, other)
        results.append((other, score))

    # Sort by best score
    results.sort(key=lambda x: x[1], reverse=True)

    return results


def create_match(user1_id, user2_id):
    """Create a new match request if not exists."""
    existing = Match.query.filter(
        ((Match.user1_id == user1_id) & (Match.user2_id == user2_id)) |
        ((Match.user1_id == user2_id) & (Match.user2_id == user1_id))
    ).first()

    if existing:
        return {"error": "Match already exists"}, 400

    match = Match(
        user1_id=user1_id,
        user2_id=user2_id,
        status="pending"
    )
    db.session.add(match)
    db.session.commit()

    return {
        "message": "Match created",
        "match_id": match.id
    }, 201


def get_user_matches(user_id):
    """Retrieve all matches for a user."""
    matches = Match.query.filter(
        (Match.user1_id == user_id) | (Match.user2_id == user_id)
    ).all()

    result = []
    for m in matches:
        other_id = m.user2_id if m.user1_id == user_id else m.user1_id
        other_user = User.query.get(other_id)

        result.append({
            "match_id": m.id,
            "status": m.status,
            "user": {
                "id": other_user.id,
                "name": other_user.name,
                "age": other_user.age,
                "gender": other_user.gender,
                "occupation": other_user.occupation,
                "budget": other_user.budget,
                "habits": json.loads(other_user.habits),
                "interests": json.loads(other_user.interests),
                "bio": other_user.bio,
                "location": other_user.location,
                "profile_picture": other_user.profile_picture,
            }
        })

    return result, 200


def update_match_status(match_id, user_id, status):
    """Update match status: accepted / rejected."""
    match = Match.query.get(match_id)
    if not match:
        return {"error": "Match not found"}, 404

    # Only the involved user can update status
    if match.user1_id != user_id and match.user2_id != user_id:
        return {"error": "Unauthorized"}, 403

    match.status = status
    db.session.commit()

    return {"message": "Match status updated"}, 200
