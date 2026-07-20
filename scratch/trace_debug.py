import os
import sys
import json

# Add backend directory to sys.path
backend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "backend")
sys.path.append(backend_dir)

from matching_engine import MatchingEngine, time_to_min

def trace():
    base_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")
    mentors_csv = os.path.join(base_dir, "mentors_prod_200_enriched.csv")
    students_csv = os.path.join(base_dir, "students_prod_2000_enriched.csv")
    
    engine = MatchingEngine(mentors_csv, students_csv)
    
    config = {
        'session_duration': 60,
        'default_same_gender': True,
        'weight_theme': 0.6,
        'weight_jaccard': 0.4,
        'poor_fit_threshold': 0.2
    }
    
    s_test = engine.raw_students[0]
    m_test = engine.raw_mentors[0]
    
    overrides = {
        'forced': [(s_test['ID'], m_test['ID'])],
        'blocked': [],
        'skipped_students': [],
        'skipped_mentors': []
    }
    
    results = engine.run_match(config, overrides)
    assignments = results['assignments']
    
    output = []
    # Let's find a mentor with overlapping bookings
    mentor_bookings = {}
    for a in assignments:
        mid = a['mentor_id']
        day = a['day']
        start = time_to_min(a['start_time'])
        end = start + config['session_duration']
        
        if mid not in mentor_bookings:
            mentor_bookings[mid] = []
            
        for b_day, b_start, b_end, student_id, explanation in mentor_bookings[mid]:
            if b_day == day and not (end <= b_start or start >= b_end):
                output.append(f"OVERLAP DETECTED FOR MENTOR: {a['mentor_name']} ({mid}) on {day}")
                output.append(f"  Booking 1: {b_start}-{b_end} (Student ID: {student_id}) - Explanation: {explanation}")
                output.append(f"  Booking 2: {start}-{end} (Student ID: {a['student_id']}) - Explanation: {a['explanation']}")
        mentor_bookings[mid].append((day, start, end, a['student_id'], a['explanation']))
        
    with open("scratch/trace_output.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(output))
        f.write(f"\nTotal violations: {len(output) // 3}")

if __name__ == "__main__":
    trace()
