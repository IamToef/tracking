import csv
import json
import random
import re
from collections import defaultdict

def time_to_min(t_str):
    """Converts a HH:MM time string to minutes since midnight."""
    h, m = map(int, t_str.split(':'))
    return h * 60 + m

def min_to_time(minutes):
    """Converts minutes since midnight to a HH:MM string."""
    h = minutes // 60
    m = minutes % 60
    return f"{h:02d}:{m:02d}"

# Keywords for thematic scoring
ACADEMIC_KEYWORDS = {
    'kỷ luật', 'thói quen', 'nhắc nhở', 'nhắc bài', 'quản lý thời gian', 'học tập', 
    'discipline', 'schedule', 'trì hoãn', 'lịch học', 'study habits', 'time management', 
    'academic', 'attendance', 'reschedule', 'rescheduling', 'hành vi', 'tự giác', 
    'kế hoạch', 'bài tập', 'nhắc nhở'
}

EMOTIONAL_KEYWORDS = {
    'cảm xúc', 'lo lắng', 'tự ti', 'chia sẻ', 'lắng nghe', 'emotional', 'empathy', 
    'confidence', 'an toàn', 'tin tưởng', 'đồng hành', 'stress', 'nhẹ nhàng', 'kiên nhẫn', 
    'thân thiện', 'mở lòng', 'nervous', 'opening up', 'shy', 'bình tĩnh', 'tâm sự'
}

def clean_and_tokenize(text):
    """Normalizes and tokenizes text into lowercased words, stripping punctuation."""
    if not text:
        return set()
    text = text.lower()
    # Strip punctuation
    text = re.sub(r'[^\w\s\s+]', ' ', text)
    return set(text.split())

def calculate_text_scores(s_text, m_text):
    """Calculates thematic score and Jaccard similarity between student and mentor texts."""
    s_words = clean_and_tokenize(s_text)
    m_words = clean_and_tokenize(m_text)
    
    if not s_words or not m_words:
        return 0.0, 0.0
        
    # 1. Thematic scores
    s_acad = len(s_words.intersection(ACADEMIC_KEYWORDS))
    s_emot = len(s_words.intersection(EMOTIONAL_KEYWORDS))
    
    m_acad = len(m_words.intersection(ACADEMIC_KEYWORDS))
    m_emot = len(m_words.intersection(EMOTIONAL_KEYWORDS))
    
    # Normalize
    s_tot = (s_acad + s_emot) or 1
    m_tot = (m_acad + m_emot) or 1
    
    s_acad_norm = s_acad / s_tot
    s_emot_norm = s_emot / s_tot
    m_acad_norm = m_acad / m_tot
    m_emot_norm = m_emot / m_tot
    
    theme_score = (s_acad_norm * m_acad_norm) + (s_emot_norm * m_emot_norm)
    
    # 2. Jaccard overlap
    jaccard = len(s_words.intersection(m_words)) / len(s_words.union(m_words))
    
    return theme_score, jaccard

def get_required_gender(student_exp, student_gender, default_same_gender):
    """Parses student expectation to find explicit gender preference."""
    exp = student_exp.lower()
    if any(phrase in exp for phrase in ['cùng giới', 'same-gender', 'same gender']):
        return student_gender
    if any(phrase in exp for phrase in ['female', 'nữ', 'nữ']):
        return 'Female'
    if any(phrase in exp for phrase in ['male', 'nam', 'nam']):
        return 'Male'
    return student_gender if default_same_gender else None

class MatchingEngine:
    def __init__(self, mentors_csv_path, students_csv_path):
        self.mentors_path = mentors_csv_path
        self.students_path = students_csv_path
        self.raw_mentors = []
        self.raw_students = []
        self.load_data()
        
    def load_data(self):
        """Loads data from CSV files."""
        # Load mentors
        with open(self.mentors_path, encoding='utf-8') as f:
            reader = csv.DictReader(f)
            self.raw_mentors = list(reader)
            
        # Load students
        with open(self.students_path, encoding='utf-8') as f:
            reader = csv.DictReader(f)
            self.raw_students = list(reader)

    def run_match(self, config, overrides):
        """Runs the matching algorithm with given config and overrides."""
        # Extract configurations
        session_duration = config.get('session_duration', 60)
        default_same_gender = config.get('default_same_gender', True)
        w_theme = config.get('weight_theme', 0.6)
        w_jaccard = config.get('weight_jaccard', 0.4)
        poor_fit_threshold = config.get('poor_fit_threshold', 0.2)
        
        # Extract overrides
        forced_dict = {f[0]: f[1] for f in overrides.get('forced', [])}
        blocked_set = set(tuple(b) for b in overrides.get('blocked', []))
        skipped_students = set(overrides.get('skipped_students', []))
        skipped_mentors = set(overrides.get('skipped_mentors', []))
        
        # Initialize Mentors
        mentors = []
        mentor_map = {}
        for rm in self.raw_mentors:
            mid = rm['ID']
            if mid in skipped_mentors:
                continue
            m = {
                'id': mid,
                'name': rm['Name'],
                'gender': rm['gender'],
                'capacity': json.loads(rm['capacity']),
                'personalities': rm['personalites'],
                'expectation': rm['expectation'],
                'bookings': [],  # list of dict: {day, start_time, end_time, student_id}
                'total_slots': 0,
                'capacity_minutes': []
            }
            # Calculate total capacity slots and pre-parse times in minutes
            for day_slots in m['capacity']:
                day = day_slots['day']
                for slot in day_slots['slots']:
                    s_min = time_to_min(slot['start_time'])
                    e_min = time_to_min(slot['end_time'])
                    m['total_slots'] += (e_min - s_min) // session_duration
                    m['capacity_minutes'].append({
                        'day': day,
                        'start': s_min,
                        'end': e_min
                    })
            mentors.append(m)
            mentor_map[mid] = m
            
        # Initialize Students
        students = []
        student_map = {}
        for rs in self.raw_students:
            sid = rs['ID']
            if sid in skipped_students:
                continue
            s = {
                'id': sid,
                'name': rs['Name'],
                'gender': rs['gender'],
                'slots': json.loads(rs['learning_slot']),
                'symptom': rs['symptom'],
                'expectation': rs['expectation']
            }
            # Pre-tokenize
            s['words'] = clean_and_tokenize(s['symptom'] + " " + s['expectation'])
            s_words = s['words']
            s['acad'] = len(s_words.intersection(ACADEMIC_KEYWORDS))
            s['emot'] = len(s_words.intersection(EMOTIONAL_KEYWORDS))
            s['tot'] = (s['acad'] + s['emot']) or 1
            
            students.append(s)
            student_map[sid] = s

        # Pre-tokenize mentors
        for m in mentors:
            m['words'] = clean_and_tokenize(m['personalities'] + " " + m['expectation'])
            m_words = m['words']
            m['acad'] = len(m_words.intersection(ACADEMIC_KEYWORDS))
            m['emot'] = len(m_words.intersection(EMOTIONAL_KEYWORDS))
            m['tot'] = (m['acad'] + m['emot']) or 1

        # Precompute the NLP compatibility matrix for O(1) lookup
        score_cache = {}
        for s in students:
            s_id = s['id']
            score_cache[s_id] = {}
            s_words = s['words']
            s_acad = s['acad']
            s_emot = s['emot']
            s_tot = s['tot']
            for m in mentors:
                m_id = m['id']
                m_words = m['words']
                
                s_acad_norm = s_acad / s_tot
                s_emot_norm = s_emot / s_tot
                m_acad_norm = m['acad'] / m['tot']
                m_emot_norm = m['emot'] / m['tot']
                theme_score = (s_acad_norm * m_acad_norm) + (s_emot_norm * m_emot_norm)
                
                intersection_len = len(s_words.intersection(m_words))
                union_len = len(s_words.union(m_words))
                jaccard = intersection_len / union_len if union_len else 0.0
                
                score_cache[s_id][m_id] = w_theme * theme_score + w_jaccard * jaccard

        # Precompute mentors by capacity for O(1) slot capacity lookup
        mentors_by_capacity = {}
        for s in students:
            for s_slot in s['slots']:
                s_day = s_slot['day']
                s_start = time_to_min(s_slot['start_time'])
                key = (s_day, s_start)
                if key not in mentors_by_capacity:
                    mentors_by_capacity[key] = []
                    s_end = s_start + session_duration
                    for m in mentors:
                        for m_slot in m['capacity_minutes']:
                            if m_slot['day'] == s_day and m_slot['start'] <= s_start and s_end <= m_slot['end']:
                                mentors_by_capacity[key].append(m)
                                break

        # Matching results
        assignments = []
        unassigned = []
        
        # 1. Separate forced students and regular students
        forced_students = []
        regular_students = []
        
        for s in students:
            if s['id'] in forced_dict:
                forced_students.append(s)
            else:
                regular_students.append(s)
                
        # 2. Process Forced Matches First
        for s in forced_students:
            target_mid = forced_dict[s['id']]
            if target_mid not in mentor_map:
                unassigned.append({
                    'student_id': s['id'],
                    'student_name': s['name'],
                    'student_gender': s['gender'],
                    'reason': f"Cố vấn được yêu cầu cưỡng ép ({target_mid}) bị bỏ qua khỏi danh sách"
                })
                continue
                
            m = mentor_map[target_mid]
            matched_slot = None
            for s_slot in s['slots']:
                s_day = s_slot['day']
                s_start = time_to_min(s_slot['start_time'])
                s_end = s_start + session_duration
                
                # Check mentor availability
                avail = False
                for m_slot in m['capacity_minutes']:
                    if m_slot['day'] == s_day and m_slot['start'] <= s_start and s_end <= m_slot['end']:
                        avail = True
                        break
                    
                if avail:
                    # Check overlap with existing bookings
                    overlap = False
                    for b in m['bookings']:
                        if b['day'] == s_day and not (s_end <= b['start_time'] or s_start >= b['end_time']):
                            overlap = True
                            break
                    if not overlap:
                        matched_slot = s_slot
                        break
            
            if matched_slot:
                s_day = matched_slot['day']
                s_start = time_to_min(matched_slot['start_time'])
                m['bookings'].append({
                    'day': s_day,
                    'start_time': s_start,
                    'end_time': s_start + session_duration,
                    'student_id': s['id']
                })
                
                score = score_cache[s['id']][m['id']]
                
                assignments.append({
                    'student_id': s['id'],
                    'student_name': s['name'],
                    'student_gender': s['gender'],
                    'mentor_id': m['id'],
                    'mentor_name': m['name'],
                    'mentor_gender': m['gender'],
                    'day': s_day,
                    'start_time': matched_slot['start_time'],
                    'end_time': min_to_time(s_start + session_duration),
                    'score': round(score, 3),
                    'is_forced': True,
                    'is_poor_fit': score < poor_fit_threshold,
                    'explanation': f"Cưỡng ép ghép đôi (Forced match) bởi Admin. Điểm tương thích: {round(score, 3)}"
                })
            else:
                unassigned.append({
                    'student_id': s['id'],
                    'student_name': s['name'],
                    'student_gender': s['gender'],
                    'reason': f"Cố vấn cưỡng ép {m['name']} không có lịch trống phù hợp với các khung giờ học của học sinh"
                })

        # 3. Process Regular Matches using improved Heuristic (MRV by compatible mentor-slots count)
        # Helper to compute number of compatible slots for a student
        def get_compatible_slots_count(s):
            req_gender = get_required_gender(s['expectation'], s['gender'], default_same_gender)
            count = 0
            for s_slot in s['slots']:
                s_day = s_slot['day']
                s_start = time_to_min(s_slot['start_time'])
                key = (s_day, s_start)
                for m in mentors_by_capacity.get(key, []):
                    if req_gender and m['gender'] != req_gender:
                        continue
                    if (s['id'], m['id']) in blocked_set:
                        continue
                    count += 1
            return count

        # Sort regular students by actual number of compatible options
        for s in regular_students:
            s['comp_count'] = get_compatible_slots_count(s)
        regular_students.sort(key=lambda s: s['comp_count'])
        
        for s in regular_students:
            req_gender = get_required_gender(s['expectation'], s['gender'], default_same_gender)
            candidates = []
            
            for s_slot in s['slots']:
                s_day = s_slot['day']
                s_start = time_to_min(s_slot['start_time'])
                s_end = s_start + session_duration
                key = (s_day, s_start)
                
                for m in mentors_by_capacity.get(key, []):
                    if req_gender and m['gender'] != req_gender:
                        continue
                    if (s['id'], m['id']) in blocked_set:
                        continue
                    
                    # Check booking overlap
                    overlap = False
                    for b in m['bookings']:
                        if b['day'] == s_day and not (s_end <= b['start_time'] or s_start >= b['end_time']):
                            overlap = True
                            break
                    if not overlap:
                        score = score_cache[s['id']][m['id']]
                        candidates.append({
                            'mentor': m,
                            'slot': s_slot,
                            'score': score
                        })
                            
            if candidates:
                candidates.sort(key=lambda x: x['score'], reverse=True)
                best = candidates[0]
                
                m = best['mentor']
                s_slot = best['slot']
                s_day = s_slot['day']
                s_start = time_to_min(s_slot['start_time'])
                score = best['score']
                
                m['bookings'].append({
                    'day': s_day,
                    'start_time': s_start,
                    'end_time': s_start + session_duration,
                    'student_id': s['id']
                })
                
                gender_req_text = f"Yêu cầu: {req_gender}" if req_gender else "Không yêu cầu giới tính"
                explanation = (
                    f"Trùng lịch {s_day.capitalize()} {s_slot['start_time']}. "
                    f"Giới tính cố vấn ({m['gender']}) đáp ứng ({gender_req_text}). "
                    f"Điểm tương thích kỳ vọng: {round(score, 3)}."
                )
                
                assignments.append({
                    'student_id': s['id'],
                    'student_name': s['name'],
                    'student_gender': s['gender'],
                    'mentor_id': m['id'],
                    'mentor_name': m['name'],
                    'mentor_gender': m['gender'],
                    'day': s_day,
                    'start_time': s_slot['start_time'],
                    'end_time': min_to_time(s_start + session_duration),
                    'score': round(score, 3),
                    'is_forced': False,
                    'is_poor_fit': score < poor_fit_threshold,
                    'explanation': explanation
                })
            else:
                # 1-step swap algorithm: Try to displace another matched student to a free alternative
                swapped = False
                for s_slot in s['slots']:
                    s_day = s_slot['day']
                    s_start = time_to_min(s_slot['start_time'])
                    s_end = s_start + session_duration
                    key = (s_day, s_start)
                    
                    for m in mentors_by_capacity.get(key, []):
                        if req_gender and m['gender'] != req_gender:
                            continue
                        if (s['id'], m['id']) in blocked_set:
                            continue
                            
                        # Find all bookings that block this slot
                        overlapping_bookings = []
                        for b in m['bookings']:
                            if b['day'] == s_day and not (s_end <= b['start_time'] or s_start >= b['end_time']):
                                overlapping_bookings.append(b)
                                
                        if len(overlapping_bookings) == 1:
                            blocking_booking = overlapping_bookings[0]
                            occupy_sid = blocking_booking['student_id']
                            # Check if the occupying student is forced
                            is_occupy_forced = any(a['student_id'] == occupy_sid and a.get('is_forced') for a in assignments)
                            if is_occupy_forced:
                                continue
                                
                            s_occupy = student_map.get(occupy_sid)
                            if not s_occupy:
                                continue
                                
                            s_occupy_req_gender = get_required_gender(s_occupy['expectation'], s_occupy['gender'], default_same_gender)
                            alternative_found = False
                            alt_m = None
                            alt_slot = None
                            alt_score = 0
                            
                            for alt_s_slot in s_occupy['slots']:
                                alt_day = alt_s_slot['day']
                                alt_start = time_to_min(alt_s_slot['start_time'])
                                alt_end = alt_start + session_duration
                                
                                for m_alt in mentors_by_capacity.get((alt_day, alt_start), []):
                                    if s_occupy_req_gender and m_alt['gender'] != s_occupy_req_gender:
                                        continue
                                    if (s_occupy['id'], m_alt['id']) in blocked_set:
                                        continue
                                    if m_alt['id'] == m['id']:
                                        # alt_slot must not overlap with s_slot
                                        if alt_day == s_day and not (alt_end <= s_start or alt_start >= s_end):
                                            continue
                                        
                                    alt_overlap = False
                                    for b_alt in m_alt['bookings']:
                                        if m_alt['id'] == m['id'] and b_alt['student_id'] == occupy_sid:
                                            continue
                                        if b_alt['day'] == alt_day and not (alt_end <= b_alt['start_time'] or alt_start >= b_alt['end_time']):
                                            alt_overlap = True
                                            break
                                            
                                    if not alt_overlap:
                                        alternative_found = True
                                        alt_m = m_alt
                                        alt_slot = alt_s_slot
                                        alt_score = score_cache[s_occupy['id']][m_alt['id']]
                                        break
                                if alternative_found:
                                    break
                                    
                            if alternative_found:
                                # Relocate s_occupy
                                m['bookings'].remove(blocking_booking)
                                old_assignment = next(a for a in assignments if a['student_id'] == s_occupy['id'])
                                assignments.remove(old_assignment)
                                
                                alt_m['bookings'].append({
                                    'day': alt_slot['day'],
                                    'start_time': time_to_min(alt_slot['start_time']),
                                    'end_time': time_to_min(alt_slot['start_time']) + session_duration,
                                    'student_id': s_occupy['id']
                                })
                                assignments.append({
                                    'student_id': s_occupy['id'],
                                    'student_name': s_occupy['name'],
                                    'student_gender': s_occupy['gender'],
                                    'mentor_id': alt_m['id'],
                                    'mentor_name': alt_m['name'],
                                    'mentor_gender': alt_m['gender'],
                                    'day': alt_slot['day'],
                                    'start_time': alt_slot['start_time'],
                                    'end_time': min_to_time(time_to_min(alt_slot['start_time']) + session_duration),
                                    'score': round(alt_score, 3),
                                    'is_forced': False,
                                    'is_poor_fit': alt_score < poor_fit_threshold,
                                    'explanation': f"Cực dịch chuyển từ {m['name']} sang {alt_m['name']} để nhường lịch. Điểm tương thích: {round(alt_score, 3)}"
                                })
                                
                                # Match s
                                m['bookings'].append({
                                    'day': s_day,
                                    'start_time': s_start,
                                    'end_time': s_start + session_duration,
                                    'student_id': s['id']
                                })
                                score = score_cache[s['id']][m['id']]
                                assignments.append({
                                    'student_id': s['id'],
                                    'student_name': s['name'],
                                    'student_gender': s['gender'],
                                    'mentor_id': m['id'],
                                    'mentor_name': m['name'],
                                    'mentor_gender': m['gender'],
                                    'day': s_day,
                                    'start_time': s_slot['start_time'],
                                    'end_time': min_to_time(s_start + session_duration),
                                    'score': round(score, 3),
                                    'is_forced': False,
                                    'is_poor_fit': score < poor_fit_threshold,
                                    'explanation': f"Xếp lịch bằng cơ chế hoán đổi (Swap) với {s_occupy['name']}. Trùng lịch {s_day.capitalize()} {s_slot['start_time']}. Điểm tương thích: {round(score, 3)}"
                                })
                                swapped = True
                                break
                    if swapped:
                        break
                        
                if not swapped:
                    # Diagnose failure reason
                    has_time = False
                    has_gender = False
                    for s_slot in s['slots']:
                        s_day = s_slot['day']
                        s_start = time_to_min(s_slot['start_time'])
                        s_end = s_start + session_duration
                        for m in mentors:
                            if (s['id'], m['id']) in blocked_set:
                                continue
                            for m_slot in m['capacity_minutes']:
                                if m_slot['day'] == s_day and m_slot['start'] <= s_start and s_end <= m_slot['end']:
                                    has_time = True
                                    if not req_gender or m['gender'] == req_gender:
                                        has_gender = True
                                        break
                    
                    if not has_time:
                        reason = "Không có cố vấn nào đăng ký rảnh vào các khung giờ lựa chọn của học sinh"
                    elif not has_gender:
                        reason = f"Có lịch trống phù hợp nhưng sai giới tính yêu cầu ({req_gender})"
                    else:
                        reason = "Tất cả cố vấn phù hợp đều đã kín lịch vào khung giờ này"
                        
                    unassigned.append({
                        'student_id': s['id'],
                        'student_name': s['name'],
                        'student_gender': s['gender'],
                        'slots': s['slots'],
                        'reason': reason
                    })
                    
        # 4. Generate Baseline Matching for comparison (Greedy pick first match, no score optimization)
        baseline_assignments = self.run_baseline(config, overrides)
        
        # 5. Compile report metrics
        report = self.generate_report(assignments, unassigned, baseline_assignments, students, mentors, poor_fit_threshold)
        
        return {
            'assignments': assignments,
            'unassigned': unassigned,
            'report': report
        }

    def run_baseline(self, config, overrides):
        """Runs a baseline greedy matching algorithm (first fit) for comparison."""
        session_duration = config.get('session_duration', 60)
        default_same_gender = config.get('default_same_gender', True)
        
        forced_dict = {f[0]: f[1] for f in overrides.get('forced', [])}
        blocked_set = set(tuple(b) for b in overrides.get('blocked', []))
        skipped_students = set(overrides.get('skipped_students', []))
        skipped_mentors = set(overrides.get('skipped_mentors', []))
        
        # Setup mentors
        mentors = []
        mentor_map = {}
        for rm in self.raw_mentors:
            mid = rm['ID']
            if mid in skipped_mentors:
                continue
            m = {
                'id': mid,
                'name': rm['Name'],
                'gender': rm['gender'],
                'capacity': json.loads(rm['capacity']),
                'bookings': [],
                'capacity_minutes': []
            }
            for day_slots in m['capacity']:
                day = day_slots['day']
                for slot in day_slots['slots']:
                    m['capacity_minutes'].append({
                        'day': day,
                        'start': time_to_min(slot['start_time']),
                        'end': time_to_min(slot['end_time'])
                    })
            mentors.append(m)
            mentor_map[mid] = m
            
        # Setup students
        students = []
        for rs in self.raw_students:
            sid = rs['ID']
            if sid in skipped_students:
                continue
            students.append({
                'id': sid,
                'name': rs['Name'],
                'gender': rs['gender'],
                'slots': json.loads(rs['learning_slot']),
                'expectation': rs['expectation']
            })
            
        assignments = []
        
        # Forced first
        for s in students:
            if s['id'] in forced_dict:
                target_mid = forced_dict[s['id']]
                if target_mid in mentor_map:
                    m = mentor_map[target_mid]
                    matched_slot = None
                    for s_slot in s['slots']:
                        s_day = s_slot['day']
                        s_start = time_to_min(s_slot['start_time'])
                        s_end = s_start + session_duration
                        
                        avail = False
                        for m_slot in m['capacity_minutes']:
                            if m_slot['day'] == s_day and m_slot['start'] <= s_start and s_end <= m_slot['end']:
                                avail = True
                                break
                        if avail:
                            overlap = False
                            for b in m['bookings']:
                                if b['day'] == s_day and not (s_end <= b['start_time'] or s_start >= b['end_time']):
                                    overlap = True
                                    break
                            if not overlap:
                                matched_slot = s_slot
                                break
                    if matched_slot:
                        m['bookings'].append({
                            'day': matched_slot['day'],
                            'start_time': time_to_min(matched_slot['start_time']),
                            'end_time': time_to_min(matched_slot['start_time']) + session_duration
                        })
                        assignments.append((s['id'], m['id']))
                        
        # Regular
        for s in students:
            if s['id'] in forced_dict:
                continue
            req_gender = get_required_gender(s['expectation'], s['gender'], default_same_gender)
            matched = False
            for s_slot in s['slots']:
                s_day = s_slot['day']
                s_start = time_to_min(s_slot['start_time'])
                s_end = s_start + session_duration
                
                for m in mentors:
                    if req_gender and m['gender'] != req_gender:
                        continue
                    if (s['id'], m['id']) in blocked_set:
                        continue
                    
                    avail = False
                    for m_slot in m['capacity_minutes']:
                        if m_slot['day'] == s_day and m_slot['start'] <= s_start and s_end <= m_slot['end']:
                            avail = True
                            break
                    if avail:
                        overlap = False
                        for b in m['bookings']:
                            if b['day'] == s_day and not (s_end <= b['start_time'] or s_start >= b['end_time']):
                                overlap = True
                                break
                        if not overlap:
                            m['bookings'].append({
                                'day': s_day,
                                'start_time': s_start,
                                'end_time': s_end
                            })
                            assignments.append((s['id'], m['id']))
                            matched = True
                            break
                if matched:
                    break
        return assignments

    def generate_report(self, assignments, unassigned, baseline_assignments, students, mentors, poor_fit_threshold):
        """Generates statistical metrics for matched results and baseline comparison."""
        total_students = len(students)
        matched_count = len(assignments)
        unmatched_count = len(unassigned)
        
        # Calculate scores
        scores = [a['score'] for a in assignments]
        avg_score = round(sum(scores) / len(scores), 3) if scores else 0.0
        
        poor_fits = sum(1 for a in assignments if a['is_poor_fit'])
        
        # Baseline comparisons
        baseline_count = len(baseline_assignments)
        
        return {
            'total_students': total_students,
            'matched_count': matched_count,
            'unmatched_count': unmatched_count,
            'match_rate': round((matched_count / total_students) * 100, 2) if total_students else 0.0,
            'avg_score': avg_score,
            'poor_fit_count': poor_fits,
            'poor_fit_rate': round((poor_fits / matched_count) * 100, 2) if matched_count else 0.0,
            'baseline_matched_count': baseline_count,
            'baseline_match_rate': round((baseline_count / total_students) * 100, 2) if total_students else 0.0,
            'improvement_vs_baseline_pct': round(((matched_count - baseline_count) / (baseline_count or 1)) * 100, 2)
        }

    def simulate_rejection(self, current_assignments, config, overrides, seed=None):
        """Simulates 20% of matched students rejecting their mentors and re-matching them (Q4)."""
        if seed is not None:
            random.seed(seed)
            
        session_duration = config.get('session_duration', 60)
        default_same_gender = config.get('default_same_gender', True)
        w_theme = config.get('weight_theme', 0.6)
        w_jaccard = config.get('weight_jaccard', 0.4)
        poor_fit_threshold = config.get('poor_fit_threshold', 0.2)
        
        forced_dict = {f[0]: f[1] for f in overrides.get('forced', [])}
        blocked_set = set(tuple(b) for b in overrides.get('blocked', []))
        skipped_students = set(overrides.get('skipped_students', []))
        skipped_mentors = set(overrides.get('skipped_mentors', []))
        
        if not current_assignments:
            return {'assignments': [], 'unassigned': [], 'rejection_report': {}}
            
        # 1. Randomly select ~20% of current assignments for rejection
        # Filter out forced matches (admin forces them, so they shouldn't reject)
        rejectable = [a for a in current_assignments if not a['is_forced']]
        num_reject = max(1, int(len(rejectable) * 0.20))
        rejected_pairs = random.sample(rejectable, min(num_reject, len(rejectable)))
        rejected_student_ids = set(r['student_id'] for r in rejected_pairs)
        
        # 2. Re-initialize mentors and their bookings from the RETAINED assignments
        mentors = []
        mentor_map = {}
        for rm in self.raw_mentors:
            mid = rm['ID']
            if mid in skipped_mentors:
                continue
            m = {
                'id': mid,
                'name': rm['Name'],
                'gender': rm['gender'],
                'capacity': json.loads(rm['capacity']),
                'personalities': rm['personalites'],
                'expectation': rm['expectation'],
                'bookings': [],
                'capacity_minutes': []
            }
            # Pre-parse capacity slots in minutes
            for day_slots in m['capacity']:
                day = day_slots['day']
                for slot in day_slots['slots']:
                    m['capacity_minutes'].append({
                        'day': day,
                        'start': time_to_min(slot['start_time']),
                        'end': time_to_min(slot['end_time'])
                    })
            # Pre-tokenize
            m['words'] = clean_and_tokenize(m['personalities'] + " " + m['expectation'])
            m_words = m['words']
            m['acad'] = len(m_words.intersection(ACADEMIC_KEYWORDS))
            m['emot'] = len(m_words.intersection(EMOTIONAL_KEYWORDS))
            m['tot'] = (m['acad'] + m['emot']) or 1
            
            mentors.append(m)
            mentor_map[mid] = m
            
        students = []
        student_map = {}
        for rs in self.raw_students:
            sid = rs['ID']
            if sid in skipped_students:
                continue
            s = {
                'id': sid,
                'name': rs['Name'],
                'gender': rs['gender'],
                'slots': json.loads(rs['learning_slot']),
                'symptom': rs['symptom'],
                'expectation': rs['expectation']
            }
            # Pre-tokenize
            s['words'] = clean_and_tokenize(s['symptom'] + " " + s['expectation'])
            s_words = s['words']
            s['acad'] = len(s_words.intersection(ACADEMIC_KEYWORDS))
            s['emot'] = len(s_words.intersection(EMOTIONAL_KEYWORDS))
            s['tot'] = (s['acad'] + s['emot']) or 1
            
            students.append(s)
            student_map[sid] = s

        # Precompute ma trận điểm số
        score_cache = {}
        for s in students:
            s_id = s['id']
            score_cache[s_id] = {}
            s_words = s['words']
            s_acad = s['acad']
            s_emot = s['emot']
            s_tot = s['tot']
            for m in mentors:
                m_id = m['id']
                m_words = m['words']
                
                s_acad_norm = s_acad / s_tot
                s_emot_norm = s_emot / s_tot
                m_acad_norm = m['acad'] / m['tot']
                m_emot_norm = m['emot'] / m['tot']
                theme_score = (s_acad_norm * m_acad_norm) + (s_emot_norm * m_emot_norm)
                
                intersection_len = len(s_words.intersection(m_words))
                union_len = len(s_words.union(m_words))
                jaccard = intersection_len / union_len if union_len else 0.0
                
                score_cache[s_id][m_id] = w_theme * theme_score + w_jaccard * jaccard

        # Re-apply bookings for students who did NOT reject
        new_assignments = []
        for a in current_assignments:
            if a['student_id'] not in rejected_student_ids:
                m = mentor_map[a['mentor_id']]
                s_start = time_to_min(a['start_time'])
                m['bookings'].append({
                    'day': a['day'],
                    'start_time': s_start,
                    'end_time': s_start + session_duration,
                    'student_id': a['student_id']
                })
                new_assignments.append(a)

        # 3. For each rejected student, run re-matching
        rejected_students = [student_map[sid] for sid in rejected_student_ids]
        
        # Keep track of who rejected whom to avoid matching back to the same mentor
        rejected_relations = {r['student_id']: r['mentor_id'] for r in rejected_pairs}
        
        # Sort rejected students by actual number of compatible options
        def get_compatible_slots_count_rejection(s):
            req_gender = get_required_gender(s['expectation'], s['gender'], default_same_gender)
            old_mentor_id = rejected_relations[s['id']]
            count = 0
            for s_slot in s['slots']:
                s_day = s_slot['day']
                s_start = time_to_min(s_slot['start_time'])
                s_end = s_start + session_duration
                for m in mentors:
                    if m['id'] == old_mentor_id:
                        continue
                    if req_gender and m['gender'] != req_gender:
                        continue
                    if (s['id'], m['id']) in blocked_set:
                        continue
                    # Check availability
                    for m_slot in m['capacity_minutes']:
                        if m_slot['day'] == s_day and m_slot['start'] <= s_start and s_end <= m_slot['end']:
                            count += 1
                            break
            return count
        
        for s in rejected_students:
            s['comp_count'] = get_compatible_slots_count_rejection(s)
        rejected_students.sort(key=lambda s: s['comp_count'])
        
        unassigned_after_rejection = []
        
        for s in rejected_students:
            req_gender = get_required_gender(s['expectation'], s['gender'], default_same_gender)
            old_mentor_id = rejected_relations[s['id']]
            
            candidates = []
            for s_slot in s['slots']:
                s_day = s_slot['day']
                s_start = time_to_min(s_slot['start_time'])
                s_end = s_start + session_duration
                
                for m in mentors:
                    if m['id'] == old_mentor_id:
                        continue
                    if req_gender and m['gender'] != req_gender:
                        continue
                    if (s['id'], m['id']) in blocked_set:
                        continue
                        
                    # Check availability
                    avail = False
                    for m_slot in m['capacity_minutes']:
                        if m_slot['day'] == s_day and m_slot['start'] <= s_start and s_end <= m_slot['end']:
                            avail = True
                            break
                        
                    if avail:
                        overlap = False
                        for b in m['bookings']:
                            if b['day'] == s_day and not (s_end <= b['start_time'] or s_start >= b['end_time']):
                                overlap = True
                                break
                        if not overlap:
                            score = score_cache[s['id']][m['id']]
                            candidates.append({
                                'mentor': m,
                                'slot': s_slot,
                                'score': score
                            })
                            
            if candidates:
                candidates.sort(key=lambda x: x['score'], reverse=True)
                best = candidates[0]
                m = best['mentor']
                s_slot = best['slot']
                s_day = s_slot['day']
                s_start = time_to_min(s_slot['start_time'])
                score = best['score']
                
                m['bookings'].append({
                    'day': s_day,
                    'start_time': s_start,
                    'end_time': s_start + session_duration,
                    'student_id': s['id']
                })
                
                gender_req_text = f"Yêu cầu: {req_gender}" if req_gender else "Không yêu cầu giới tính"
                explanation = (
                    f"Ghép đôi lại (Re-matched) sau từ chối. Trùng lịch {s_day.capitalize()} {s_slot['start_time']}. "
                    f"Giới tính cố vấn ({m['gender']}) đáp ứng ({gender_req_text}). "
                    f"Cố vấn trước đó ({mentor_map[old_mentor_id]['name']}) bị từ chối. "
                    f"Điểm tương thích kỳ vọng mới: {round(score, 3)}."
                )
                
                new_assignments.append({
                    'student_id': s['id'],
                    'student_name': s['name'],
                    'student_gender': s['gender'],
                    'mentor_id': m['id'],
                    'mentor_name': m['name'],
                    'mentor_gender': m['gender'],
                    'day': s_day,
                    'start_time': s_slot['start_time'],
                    'end_time': min_to_time(s_start + session_duration),
                    'score': round(score, 3),
                    'is_forced': False,
                    'is_poor_fit': score < poor_fit_threshold,
                    'explanation': explanation,
                    'is_rematched': True,
                    'old_mentor_name': mentor_map[old_mentor_id]['name']
                })
            else:
                # Could not re-match
                unassigned_after_rejection.append({
                    'student_id': s['id'],
                    'student_name': s['name'],
                    'student_gender': s['gender'],
                    'reason': f"Học sinh từ chối cố vấn {mentor_map[old_mentor_id]['name']} nhưng không tìm thấy cố vấn thay thế trống lịch phù hợp."
                })
                
        # 4. Compile metrics after rejection
        total_students = len(students)
        matched_count = len(new_assignments)
        scores = [a['score'] for a in new_assignments]
        avg_score = round(sum(scores) / len(scores), 3) if scores else 0.0
        poor_fits = sum(1 for a in new_assignments if a['is_poor_fit'])
        
        rejection_report = {
            'rejected_count': len(rejected_pairs),
            'rematched_success_count': len(rejected_student_ids) - len(unassigned_after_rejection),
            'rematched_fail_count': len(unassigned_after_rejection),
            'matched_count_after': matched_count,
            'match_rate_after': round((matched_count / total_students) * 100, 2),
            'avg_score_after': avg_score,
            'poor_fit_count_after': poor_fits,
            'poor_fit_rate_after': round((poor_fits / matched_count) * 100, 2) if matched_count else 0.0
        }
        
        return {
            'assignments': new_assignments,
            'unassigned': unassigned_after_rejection,
            'rejection_report': rejection_report
        }
