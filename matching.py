from models import db, User, Match
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
