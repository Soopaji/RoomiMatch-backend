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
<<<<<<< HEAD
    """Update match status: accepted / rejected."""
    match = Match.query.get(match_id)
    if not match:
        return {"error": "Match not found"}, 404
=======
    """Update match status (accept/reject)"""from models import db, User, Match
import json
from sqlalchemy import or_, and_

def calculate_match_score(user1, user2):
    """Calculate compatibility score between two users"""
    score = 0

    # Age compatibility (closer ages get higher score)
    age_diff = abs(user1.age - user2.age)
    if age_diff <= 2:
        score += 30
    elif age_diff <= 5:
        score += 20
    elif age_diff <= 10:
        score += 10

    # Budget compatibility
    if user1.budget == user2.budget:
        score += 25

    # Habits compatibility
    user1_habits = set(json.loads(user1.habits))
    user2_habits = set(json.loads(user2.habits))

    # Shared habits
    shared_habits = user1_habits.intersection(user2_habits)
    score += len(shared_habits) * 5

    # Interests compatibility
    user1_interests = set(json.loads(user1.interests))
    user2_interests = set(json.loads(user2.interests))

    shared_interests = user1_interests.intersection(user2_interests)
    score += len(shared_interests) * 8

    return min(score, 100)  # Cap at 100

def find_potential_matches(user_id, filters=None, limit=20):
    """Find potential matches for a user based on filters and compatibility"""
    user = User.query.get(user_id)
    if not user:
        return []

    # Base query excluding current user and existing matches
    existing_match_user_ids = db.session.query(
        db.case(
            (Match.user1_id == user_id, Match.user2_id),
            else_=Match.user1_id
        )
    ).filter(
        or_(Match.user1_id == user_id, Match.user2_id == user_id)
    ).subquery()

    query = User.query.filter(
        User.id != user_id,
        ~User.id.in_(existing_match_user_ids)
    )

    # Apply filters
    if filters:
        if filters.get('gender') and filters['gender'] != 'Any':
            query = query.filter(User.gender == filters['gender'])

        if filters.get('min_age'):
            query = query.filter(User.age >= filters['min_age'])

        if filters.get('max_age'):
            query = query.filter(User.age <= filters['max_age'])

        if filters.get('budget') and filters['budget'] != 'Any':
            query = query.filter(User.budget == filters['budget'])

        if filters.get('location'):
            query = query.filter(User.location.ilike(f"%{filters['location']}%"))

    # Get candidates
    candidates = query.limit(limit * 2).all()  # Get more candidates for scoring

    # Calculate scores and sort
    scored_candidates = []
    for candidate in candidates:
        score = calculate_match_score(user, candidate)
        scored_candidates.append((candidate, score))

    # Sort by score descending and return top matches
    scored_candidates.sort(key=lambda x: x[1], reverse=True)

    return scored_candidates[:limit]

def create_match(user1_id, user2_id):
    """Create a new match between two users"""
    try:
        # Check if match already exists
        existing_match = Match.query.filter(
            or_(
                and_(Match.user1_id == user1_id, Match.user2_id == user2_id),
                and_(Match.user1_id == user2_id, Match.user2_id == user1_id)
            )
        ).first()

        if existing_match:
            return {'error': 'Match already exists'}, 400

        match = Match(user1_id=user1_id, user2_id=user2_id, status='pending')
        db.session.add(match)
        db.session.commit()

        return {
            'message': 'Match created successfully',
            'match_id': match.id
        }, 201

    except Exception as e:
        db.session.rollback()
        return {'error': str(e)}, 500

def get_user_matches(user_id):
    """Get all matches for a user"""
    try:
        matches = Match.query.filter(
            or_(Match.user1_id == user_id, Match.user2_id == user_id)
        ).all()

        match_data = []
        for match in matches:
            other_user_id = match.user2_id if match.user1_id == user_id else match.user1_id
            other_user = User.query.get(other_user_id)

            match_data.append({
                'match_id': match.id,
                'user': {
                    'id': other_user.id,
                    'name': other_user.name,
                    'age': other_user.age,
                    'occupation': other_user.occupation,
                    'profile_picture': other_user.profile_picture
                },
                'status': match.status,
                'created_at': match.created_at.isoformat()
            })

        return match_data, 200

    except Exception as e:
        return {'error': str(e)}, 500

def update_match_status(match_id, user_id, status):
    """Update match status (accept/reject)"""
    try:
        match = Match.query.get(match_id)
>>>>>>> 483f97c5f8728f4197c9024f4a9401aa32c52756

    # Only the involved user can update status
    if match.user1_id != user_id and match.user2_id != user_id:
        return {"error": "Unauthorized"}, 403

    match.status = status
    db.session.commit()

<<<<<<< HEAD
    return {"message": "Match status updated"}, 200
=======
        match.status = status
        db.session.commit()

        return {'message': f'Match {status}'}, 200

    except Exception as e:
        db.session.rollback()
        return {'error': str(e)}, 500

    try:
        match = Match.query.get(match_id)

        if not match:
            return {'error': 'Match not found'}, 404

        # Ensure user is part of the match
        if user_id not in [match.user1_id, match.user2_id]:
            return {'error': 'Unauthorized'}, 403

        match.status = status
        db.session.commit()

        return {'message': f'Match {status}'}, 200

    except Exception as e:
        db.session.rollback()
        return {'error': str(e)}, 500
>>>>>>> 483f97c5f8728f4197c9024f4a9401aa32c52756
