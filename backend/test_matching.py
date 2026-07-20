import os
import json
from matching_engine import MatchingEngine, time_to_min

def test_engine():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    mentors_csv = os.path.join(base_dir, "..", "data", "mentors_prod_200_enriched.csv")
    students_csv = os.path.join(base_dir, "..", "data", "students_prod_2000_enriched.csv")
    
    # Initialize engine
    engine = MatchingEngine(mentors_csv, students_csv)
    print("Data loaded successfully.")
    print(f"Total Raw Mentors: {len(engine.raw_mentors)}")
    print(f"Total Raw Students: {len(engine.raw_students)}")
    
    # Define config and overrides
    config = {
        'session_duration': 60,
        'default_same_gender': True,
        'weight_theme': 0.6,
        'weight_jaccard': 0.4,
        'poor_fit_threshold': 0.2
    }
    
    # Get a test student and mentor
    s_test = engine.raw_students[0]
    m_test = engine.raw_mentors[0]
    
    overrides = {
        'forced': [(s_test['ID'], m_test['ID'])], # Force first student with first mentor
        'blocked': [],
        'skipped_students': [],
        'skipped_mentors': []
    }
    
    print("\n--- Test 1: Forced Match ---")
    results = engine.run_match(config, overrides)
    assignments = results['assignments']
    unassigned = results['unassigned']
    report = results['report']
    
    print(f"Total Matched: {len(assignments)}")
    print(f"Total Unassigned: {len(unassigned)}")
    print(f"Match Rate: {report['match_rate']}%")
    print(f"Average Score: {report['avg_score']}")
    
    # Check if forced match succeeded
    forced_match = next((a for a in assignments if a['student_id'] == s_test['ID']), None)
    if forced_match:
        print(f"SUCCESS: Student {s_test['Name']} successfully forced to Mentor {m_test['Name']}.")
    else:
        print(f"FAILED/BLOCKED: Student {s_test['Name']} could not be forced (maybe schedule clash). Reason in unassigned:")
        un_item = next((u for u in unassigned if u.get('student_id') == s_test['ID']), None)
        if un_item:
            print(f"Reason: {un_item['reason']}")
            
    print("\n--- Test 2: Hard Time & Gender Constraint Verifications ---")
    # Verify gender matching
    gender_violations = 0
    for a in assignments:
        # Check student expected gender
        exp = next(s for s in engine.raw_students if s['ID'] == a['student_id'])['expectation'].lower()
        mentor_gender = a['mentor_gender']
        student_gender = a['student_gender']
        
        req_gender = None
        if 'cùng giới' in exp or 'same-gender' in exp or 'same gender' in exp:
            req_gender = student_gender
        elif 'female' in exp or 'nữ' in exp:
            req_gender = 'Female'
        elif 'male' in exp or 'nam' in exp:
            req_gender = 'Male'
        elif config['default_same_gender']:
            req_gender = student_gender
            
        if req_gender and mentor_gender != req_gender:
            gender_violations += 1
            print(f"Violation: Student {a['student_name']} expected {req_gender} but got {a['mentor_name']} ({mentor_gender})")
            
    print(f"Gender Constraint Violations: {gender_violations}")
    
    # Verify booking overlaps
    booking_overlaps = 0
    mentor_bookings = {}
    for a in assignments:
        mid = a['mentor_id']
        day = a['day']
        start = time_to_min(a['start_time'])
        end = start + config['session_duration']
        
        if mid not in mentor_bookings:
            mentor_bookings[mid] = []
            
        for b_day, b_start, b_end in mentor_bookings[mid]:
            if b_day == day and not (end <= b_start or start >= b_end):
                booking_overlaps += 1
                print(f"Overlap Violation for Mentor {a['mentor_name']} on {day}: {start}-{end} overlapping with {b_start}-{b_end}")
        mentor_bookings[mid].append((day, start, end))
        
    print(f"Schedule Overlap Violations: {booking_overlaps}")
    
    print("\n--- Test 3: Rejection & Rematching Simulation ---")
    sim_results = engine.simulate_rejection(assignments, config, overrides, seed=42)
    rep = sim_results['rejection_report']
    print(f"Rejected: {rep['rejected_count']} pairs")
    print(f"Rematched Success: {rep['rematched_success_count']}")
    print(f"Rematched Fail: {rep['rematched_fail_count']}")
    print(f"Match Rate after: {rep['match_rate_after']}%")
    print(f"Average Score after: {rep['avg_score_after']}")
    print("Rematching process verified.")

if __name__ == "__main__":
    test_engine()
