import pandas as pd
import numpy as np

class PfitzRunClassifier:
    def __init__(self, max_hr=191):
        self.max_hr = max_hr
        
        # Known personal best paces (untracked but known)
        # 20 min 5K = 4.0 min/km, 42 min 10K = 4.2 min/km
        self.known_pb_5k_pace = 4.0  # 20 minutes / 5km
        self.known_pb_10k_pace = 4.2  # 42 minutes / 10km
        
        # Tracked personal best paces (will be calculated from data)
        self.tracked_pb_5k_pace = None
        self.tracked_pb_10k_pace = None
        
    def calculate_personal_bests(self, df):
        """Calculate tracked personal best paces from best efforts data"""
        # Get best tracked 5K pace from best efforts
        if '5k_pace_min_per_km' in df.columns:
            best_5k = df['5k_pace_min_per_km'].dropna()
            if len(best_5k) > 0:
                self.tracked_pb_5k_pace = best_5k.min()
        
        # Get best tracked 10K pace from best efforts  
        if '10k_pace_min_per_km' in df.columns:
            best_10k = df['10k_pace_min_per_km'].dropna()
            if len(best_10k) > 0:
                self.tracked_pb_10k_pace = best_10k.min()
        
        print(f"Personal Bests:")
        print(f"- Known 5K PB: {self.known_pb_5k_pace:.2f} min/km (20:00 race)")
        print(f"- Known 10K PB: {self.known_pb_10k_pace:.2f} min/km (42:00 race)")
        print(f"- Tracked 5K best: {self.tracked_pb_5k_pace:.2f} min/km" if self.tracked_pb_5k_pace else "- Tracked 5K best: Not available")
        print(f"- Tracked 10K best: {self.tracked_pb_10k_pace:.2f} min/km" if self.tracked_pb_10k_pace else "- Tracked 10K best: Not available")
        
    def classify_run(self, row):
        """Classify a single run based on improved Pfitzinger framework"""
        distance_km = row['distance_km']
        pace_min_per_km = row['pace_min_per_km']
        avg_hr = row.get('average_heartrate', 0)
        max_hr_run = row.get('max_heartrate', 0)
        duration_min = row['duration_min']
        
        # Get best efforts for this run
        pace_2_mile = row.get('2_mile_pace_min_per_km')
        pace_1k = row.get('1k_pace_min_per_km') 
        pace_5k = row.get('5k_pace_min_per_km')
        pace_10k = row.get('10k_pace_min_per_km')
        
        # Calculate HR percentages if HR data available
        avg_hr_pct = (avg_hr / self.max_hr * 100) if avg_hr > 0 else 0
        max_hr_pct = (max_hr_run / self.max_hr * 100) if max_hr_run > 0 else 0
        
        # Classification logic using improved rules (in training intensity order)
        
        # 1. RACES - Using best efforts compared to PBs
        if self._is_race(pace_5k, pace_10k):
            return "Race"
        
        # 2. VO2 MAX INTERVALS - Using max HR and 1K best effort
        if self._is_vo2_max_intervals(pace_1k, max_hr_pct):
            return "VO₂ Max Intervals"
        
        # 3. LACTATE THRESHOLD - Using max HR and 2-mile best effort
        if self._is_lactate_threshold(pace_2_mile, max_hr_pct):
            return "Lactate Threshold"
        
        # 4. RECOVERY RUNS
        if self._is_recovery_run(distance_km, avg_hr_pct):
            return "Recovery"
        
        # 5. ENDURANCE RUNS
        if self._is_endurance_run(distance_km, duration_min):
            return "Endurance"
        
        # 6. GENERAL AEROBIC RUNS
        if self._is_general_aerobic(distance_km, avg_hr_pct, duration_min):
            return "General Aerobic"
        
        # 7. OTHER - Everything else (for investigation)
        return "Other"
    
    def _is_race(self, pace_5k, pace_10k):
        """Detect races using pace rules"""
        # 5k best effort pace per km < 5km PB pace per km + 10 seconds = Race 
        if pace_5k and self.known_pb_5k_pace:
            if pace_5k <= self.known_pb_5k_pace + 0.17:  # +10 seconds = +0.17 min
                return True
                
        # 10k best effort pace per km < 10km PB pace per km + 10 seconds = Race
        if pace_10k and self.known_pb_10k_pace:
            if pace_10k <= self.known_pb_10k_pace + 0.17:  # +10 seconds = +0.17 min
                return True
                
        return False
    
    def _is_vo2_max_intervals(self, pace_1k, max_hr_pct):
        """Detect VO2 max intervals using max HR and 1K best effort"""
        # Max HR >= 95% OR 1k best effort pace <= 5K PB + 5 seconds
        if max_hr_pct >= 95:
            return True
            
        if pace_1k and self.known_pb_5k_pace:
            if pace_1k <= self.known_pb_5k_pace + 0.083:  # +5 seconds = +0.083 min
                return True
        
        return False
    
    def _is_lactate_threshold(self, pace_2_mile, max_hr_pct):
        """Detect lactate threshold using max HR and 2-mile best effort"""
        # Must have max HR >= 85% AND 2-mile best effort <= 10K PB + 25 seconds
        if max_hr_pct >= 85 and pace_2_mile and self.known_pb_10k_pace:
            if pace_2_mile <= self.known_pb_10k_pace + 0.42:  # +25 seconds = +0.42 min
                return True
        
        return False
    
    def _is_recovery_run(self, distance_km, avg_hr_pct):
        """Recovery: Distance <= 8km AND avg HR < 70%"""
        return (distance_km <= 8.0 and avg_hr_pct < 70 and avg_hr_pct > 0)
    
    def _is_endurance_run(self, distance_km, duration_min):
        """Endurance: Distance >= 12km AND duration >= 60 minutes"""
        return (distance_km >= 12 and duration_min >= 60)
    
    def _is_general_aerobic(self, distance_km, avg_hr_pct, duration_min):
        """General Aerobic: 3-12km, 15+ min duration, 70-81% avg HR"""
        return (distance_km >= 3 and distance_km < 12 and  
                duration_min >= 15 and
                avg_hr_pct >= 70 and avg_hr_pct <= 81)
    
    def classify_dataframe(self, df):
        """Classify all runs in a dataframe"""
        df = df.copy()
        
        # First calculate personal bests from the data
        self.calculate_personal_bests(df)
        
        # Then classify each run
        df['run_type'] = df.apply(self.classify_run, axis=1)
        
        return df
    
    def get_classification_summary(self, df):
        """Get summary of run type distribution"""
        classified_df = self.classify_dataframe(df)
        
        summary = classified_df.groupby('run_type').agg({
            'distance_km': ['count', 'mean'],
            'pace_min_per_km': 'mean',
            'average_heartrate': 'mean'
        }).round(2)
        
        return summary, classified_df

def analyze_your_runs():
    """Analyze your running data with improved classification"""
    # Load enhanced running data
    try:
        df = pd.read_csv('running_data.csv')
        df['date'] = pd.to_datetime(df['date'])
    except FileNotFoundError:
        print("❌ running_data.csv not found. Run fetch_activities.py first.")
        return None
    
    print(f"🏃 Analyzing {len(df)} runs with improved classification...")
    print("=" * 60)
    
    # Initialize classifier with your max HR
    classifier = PfitzRunClassifier(max_hr=191)
    
    # Get classification summary
    summary, classified_df = classifier.get_classification_summary(df)
    
    # Show classification results
    print("\n📊 Run Type Classification Results:")
    print("=" * 40)
    
    run_type_counts = classified_df['run_type'].value_counts()
    total_runs = len(classified_df)
    
    # Show in training intensity order
    intensity_order = ['Recovery', 'General Aerobic', 'Endurance', 'Lactate Threshold', 'VO₂ Max Intervals', 'Race', 'Other']
    
    for run_type in intensity_order:
        if run_type in run_type_counts:
            count = run_type_counts[run_type]
            percentage = (count / total_runs) * 100
            print(f"{run_type:20}: {count:2d} runs ({percentage:4.1f}%)")
    
    # Show recent runs with classifications
    print(f"\n🔍 Recent Run Classifications:")
    print("=" * 50)
    
    recent_runs = classified_df.tail(10)
    for _, row in recent_runs.iterrows():
        date_str = row['date'].strftime('%Y-%m-%d')
        hr_info = f" | HR: {row['average_heartrate']:.0f}" if row['average_heartrate'] > 0 else ""
        print(f"{date_str}: {row['name'][:25]:25} → {row['run_type']:15} | {row['distance_km']:.1f}km{hr_info}")
    
    # Save classified data
    classified_df.to_csv('classified_running_data.csv', index=False)
    print(f"\n💾 Classified data saved to 'classified_running_data.csv'")
    
    # Show training insights
    print(f"\n🎯 Training Distribution Insights:")
    print("=" * 40)
    
    # Base training
    base_runs = run_type_counts.get('General Aerobic', 0) + run_type_counts.get('Recovery', 0) + run_type_counts.get('Endurance', 0)
    base_pct = (base_runs / total_runs) * 100
    print(f"Base Training (GA+Recovery+Endurance): {base_runs} runs ({base_pct:.1f}%)")
    
    # Quality sessions
    quality_runs = run_type_counts.get('Lactate Threshold', 0) + run_type_counts.get('VO₂ Max Intervals', 0)
    if quality_runs > 0:
        quality_pct = (quality_runs / total_runs) * 100
        print(f"Quality Sessions (LT+VO₂): {quality_runs} runs ({quality_pct:.1f}%)")
    
    # Races
    if run_type_counts.get('Race', 0) > 0:
        race_pct = (run_type_counts['Race'] / total_runs) * 100
        print(f"Races: {run_type_counts['Race']} runs ({race_pct:.1f}%)")
    
    # Highlight 'Other' runs for investigation
    if run_type_counts.get('Other', 0) > 0:
        other_pct = (run_type_counts['Other'] / total_runs) * 100
        print(f"\n⚠️  'Other' runs need investigation: {run_type_counts['Other']} ({other_pct:.1f}%)")
        
        # Show what's in Other
        other_runs = classified_df[classified_df['run_type'] == 'Other'].tail(5)
        print("   Recent 'Other' runs:")
        for _, row in other_runs.iterrows():
            hr_info = f", HR: {row['average_heartrate']:.0f}" if row['average_heartrate'] > 0 else ", No HR"
            print(f"   • {row['date'].strftime('%m-%d')}: {row['distance_km']:.1f}km, {row['duration_min']:.0f}min{hr_info}")
    
    return classified_df

if __name__ == "__main__":
    analyze_your_runs()