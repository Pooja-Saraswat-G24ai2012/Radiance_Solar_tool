#!/usr/bin/env python3
"""
Advanced Clipping Loss Calculator with Forced PPC Methodology
==============================================================

This script implements the industry-standard 4-step algorithm:
1. Find the "Clipping Window" (when inverter hits AC capacity)
2. Calculate "Reference PR" from clean (non-clipping) periods
3. Simulate "What Should Have Been" without AC capacity limit
4. Calculate the Loss (Simulated - Actual)

Author: Automated Solar Analysis System
Version: 2.0
"""

import pandas as pd
import numpy as np
from datetime import datetime, time
import sys
import os

def find_clipping_window(df, ac_capacity, threshold=0.985):
    """
    STEP 1: Find when clipping happens
    
    Scans through the day to identify:
    - Start Point: First moment inverter reaches ~AC capacity
    - Stop Point: Last moment inverter is at ~AC capacity
    
    Args:
        df: DataFrame with 'Active_Power' column
        ac_capacity: AC capacity limit in kW
        threshold: Percentage of AC capacity to consider as clipping (default 98.5%)
    
    Returns:
        (start_idx, stop_idx) or (None, None) if no clipping found
    """
    clipping_threshold = ac_capacity * threshold
    
    # Find all points where power exceeds threshold
    clipping_mask = df['Active_Power'] >= clipping_threshold
    clipping_indices = df[clipping_mask].index.tolist()
    
    if len(clipping_indices) == 0:
        return None, None
    
    start_idx = clipping_indices[0]
    stop_idx = clipping_indices[-1]
    
    return start_idx, stop_idx


def calculate_reference_pr(df, start_idx, stop_idx, dc_capacity, 
                           num_points=10, pr_min=0.50, pr_max=0.90):
    """
    STEP 2: Calculate Reference PR (Performance Ratio)
    
    Takes data points BEFORE and AFTER clipping window to calculate
    the system's efficiency when NOT clipping.
    
    Formula: PR = Active_Power / (POA × DC_Capacity)
    
    Args:
        df: DataFrame with 'Active_Power' and 'POA' columns
        start_idx: Start of clipping window
        stop_idx: End of clipping window
        dc_capacity: DC capacity in kW
        num_points: Number of points to sample before/after (default 10)
        pr_min: Minimum acceptable PR (default 0.50)
        pr_max: Maximum acceptable PR (default 0.90)
    
    Returns:
        reference_pr: Average PR from clean periods
        pr_details: List of (index, PR) for debugging
    """
    pr_values = []
    pr_details = []
    
    # Sample points BEFORE clipping starts
    start_position = df.index.get_loc(start_idx)
    for i in range(1, num_points + 1):
        idx_pos = start_position - i
        if idx_pos >= 0:
            idx = df.index[idx_pos]
            power = df.loc[idx, 'Active_Power']
            poa = df.loc[idx, 'POA']
            
            if poa > 10:  # Only use points with meaningful irradiance
                pr = power / (poa * dc_capacity / 1000)  # POA is in W/m², need kW
                
                # Apply min/max limits
                pr = max(pr_min, min(pr_max, pr))
                
                pr_values.append(pr)
                pr_details.append(('BEFORE', idx, power, poa, pr))
    
    # Sample points AFTER clipping ends
    stop_position = df.index.get_loc(stop_idx)
    for i in range(1, num_points + 1):
        idx_pos = stop_position + i
        if idx_pos < len(df):
            idx = df.index[idx_pos]
            power = df.loc[idx, 'Active_Power']
            poa = df.loc[idx, 'POA']
            
            if poa > 10:
                pr = power / (poa * dc_capacity / 1000)
                pr = max(pr_min, min(pr_max, pr))
                
                pr_values.append(pr)
                pr_details.append(('AFTER', idx, power, poa, pr))
    
    if len(pr_values) == 0:
        return None, []
    
    reference_pr = np.mean(pr_values)
    
    return reference_pr, pr_details


def simulate_expected_power(df, start_idx, stop_idx, reference_pr, dc_capacity, 
                            ac_capacity, dc_cap_limit=0.95):
    """
    STEP 3: Simulate "What Should Have Been"
    
    For every minute during clipping window, calculates what power
    the system WOULD have produced without AC capacity constraint.
    
    Formula: Simulated_Power = Reference_PR × DC_Capacity × (POA/1000)
    
    Args:
        df: DataFrame with 'POA' column
        start_idx: Start of clipping window
        stop_idx: End of clipping window
        reference_pr: Average PR from clean periods
        dc_capacity: DC capacity in kW
        ac_capacity: AC capacity in kW
        dc_cap_limit: Maximum DC capacity utilization (default 95%)
    
    Returns:
        df: DataFrame with new 'Simulated_Power' column added
    """
    df['Simulated_Power'] = 0.0
    
    # Get the range of indices
    start_pos = df.index.get_loc(start_idx)
    stop_pos = df.index.get_loc(stop_idx)
    
    max_dc_power = dc_capacity * dc_cap_limit
    
    for pos in range(start_pos, stop_pos + 1):
        idx = df.index[pos]
        poa = df.loc[idx, 'POA']
        
        # Calculate simulated power
        simulated = reference_pr * dc_capacity * (poa / 1000)
        
        # Cap at max DC capacity
        simulated = min(simulated, max_dc_power)
        
        df.loc[idx, 'Simulated_Power'] = simulated
    
    return df


def calculate_clipping_loss(df, start_idx, stop_idx):
    """
    STEP 4: Calculate the Loss
    
    Compares Actual vs Simulated power for every minute in clipping window
    and sums up the losses.
    
    Formula: Loss = Simulated_Power - Actual_Power (when Simulated > Actual)
    
    Args:
        df: DataFrame with 'Active_Power' and 'Simulated_Power' columns
        start_idx: Start of clipping window
        stop_idx: End of clipping window
    
    Returns:
        Dictionary with loss metrics
    """
    # Get the clipping window data
    start_pos = df.index.get_loc(start_idx)
    stop_pos = df.index.get_loc(stop_idx)
    
    clipping_window = df.iloc[start_pos:stop_pos + 1].copy()
    
    # Calculate minute-by-minute loss
    clipping_window['Power_Loss_kW'] = clipping_window['Simulated_Power'] - clipping_window['Active_Power']
    clipping_window['Power_Loss_kW'] = clipping_window['Power_Loss_kW'].clip(lower=0)  # Only positive losses
    
    # Calculate energy (kWh) - power readings are per minute, so divide by 60
    total_actual_energy = clipping_window['Active_Power'].sum() / 60
    total_simulated_energy = clipping_window['Simulated_Power'].sum() / 60
    total_loss_energy = clipping_window['Power_Loss_kW'].sum() / 60
    
    # Calculate for entire day (not just clipping window)
    daily_actual_energy = df['Active_Power'].sum() / 60
    daily_simulated_energy = df['Simulated_Power'].sum() / 60
    
    # Fill simulated power for non-clipping periods (equals actual power)
    df.loc[df['Simulated_Power'] == 0, 'Simulated_Power'] = df.loc[df['Simulated_Power'] == 0, 'Active_Power']
    daily_simulated_energy_full = df['Simulated_Power'].sum() / 60
    
    # Loss percentages
    loss_pct_vs_actual = (total_loss_energy / daily_actual_energy * 100) if daily_actual_energy > 0 else 0
    loss_pct_vs_simulated = (total_loss_energy / daily_simulated_energy_full * 100) if daily_simulated_energy_full > 0 else 0
    
    # Find peak clipping moment
    peak_loss_idx = clipping_window['Power_Loss_kW'].idxmax()
    peak_loss_kw = clipping_window.loc[peak_loss_idx, 'Power_Loss_kW']
    
    # Calculate clipping duration
    clipping_duration_minutes = len(clipping_window)
    clipping_duration_hours = clipping_duration_minutes / 60
    
    results = {
        'daily_actual_energy_kwh': daily_actual_energy,
        'daily_simulated_energy_kwh': daily_simulated_energy_full,
        'clipping_loss_energy_kwh': total_loss_energy,
        'loss_pct_vs_actual': loss_pct_vs_actual,
        'loss_pct_vs_simulated': loss_pct_vs_simulated,
        'peak_loss_kw': peak_loss_kw,
        'peak_loss_time': peak_loss_idx,
        'clipping_duration_minutes': clipping_duration_minutes,
        'clipping_duration_hours': clipping_duration_hours,
        'clipping_start_time': start_idx,
        'clipping_stop_time': stop_idx,
        'clipping_window_df': clipping_window
    }
    
    return results, df


def analyze_clipping_advanced(excel_file, filter_date=None, hour_start=None, hour_end=None):
    """
    Main function to perform advanced clipping loss analysis with Forced PPC methodology
    """
    print("=" * 80)
    print("🚀 ADVANCED CLIPPING LOSS CALCULATOR - FORCED PPC METHODOLOGY")
    print("=" * 80)
    
    # Read Excel file
    print(f"\n📂 Reading file: {excel_file}")
    
    try:
        xls = pd.ExcelFile(excel_file)
        
        # Try to find the right sheet
        if 'RAW Data' in xls.sheet_names:
            sheet_name = 'RAW Data'
        elif len(xls.sheet_names) == 1:
            sheet_name = xls.sheet_names[0]
        else:
            sheet_name = xls.sheet_names[0]
        
        print(f"   Using sheet: '{sheet_name}'")
        df = pd.read_excel(excel_file, sheet_name=sheet_name)
        
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        return
    
    print(f"   Loaded {len(df)} rows")
    print(f"   Columns: {', '.join(df.columns.tolist())}")
    
    # Identify columns
    datetime_col = None
    power_col = None
    poa_col = None
    ac_cap_col = None
    dc_cap_col = None
    
    for col in df.columns:
        col_lower = str(col).lower()
        if 'datetime' in col_lower:
            datetime_col = col
        elif 'active power' in col_lower or 'active_power' in col_lower:
            power_col = col
        elif 'poa' in col_lower and 'irradiance' in col_lower:
            poa_col = col
        elif 'ac capacity' in col_lower or 'ac_capacity' in col_lower:
            ac_cap_col = col
        elif 'dc capacity' in col_lower or 'dc_capacity' in col_lower:
            dc_cap_col = col
    
    # Validate required columns
    if not all([datetime_col, power_col, poa_col, ac_cap_col, dc_cap_col]):
        print("\n❌ Missing required columns!")
        print(f"   DateTime column: {datetime_col}")
        print(f"   Active Power column: {power_col}")
        print(f"   POA Irradiance column: {poa_col}")
        print(f"   AC Capacity column: {ac_cap_col}")
        print(f"   DC Capacity column: {dc_cap_col}")
        return
    
    # Rename columns for easier handling
    df = df.rename(columns={
        datetime_col: 'DateTime',
        power_col: 'Active_Power',
        poa_col: 'POA',
        ac_cap_col: 'AC_Capacity',
        dc_cap_col: 'DC_Capacity'
    })
    
    # Parse DateTime
    df['DateTime'] = pd.to_datetime(df['DateTime'])
    df = df.set_index('DateTime')
    df = df.sort_index()
    
    # Get system parameters (use first non-null values)
    ac_capacity = df['AC_Capacity'].dropna().iloc[0]
    dc_capacity = df['DC_Capacity'].dropna().iloc[0]
    dc_ac_ratio = dc_capacity / ac_capacity
    
    print(f"\n📊 System Parameters:")
    print(f"   AC Capacity: {ac_capacity:,.2f} kW")
    print(f"   DC Capacity: {dc_capacity:,.2f} kW")
    print(f"   DC/AC Ratio: {dc_ac_ratio:.2f}")
    
    if dc_ac_ratio > 1.2:
        print(f"   ⚠️  High DC/AC ratio - Significant clipping potential!")
    
    # Apply filters
    if filter_date:
        filter_date_obj = pd.to_datetime(filter_date).date()
        df = df[df.index.date == filter_date_obj]
        print(f"\n📅 Filtered to date: {filter_date}")
        print(f"   Rows after filter: {len(df)}")
    
    if hour_start is not None and hour_end is not None:
        df = df[df.index.hour.isin(range(hour_start, hour_end))]
        print(f"\n⏰ Filtered to hours: {hour_start}:00 - {hour_end}:00")
        print(f"   Rows after filter: {len(df)}")
    
    if len(df) == 0:
        print("\n❌ No data after applying filters!")
        return
    
    # STEP 1: Find Clipping Window
    print("\n" + "=" * 80)
    print("🔍 STEP 1: Finding Clipping Window")
    print("=" * 80)
    
    start_idx, stop_idx = find_clipping_window(df, ac_capacity, threshold=0.985)
    
    if start_idx is None:
        print("✅ No clipping detected! System operating below AC capacity.")
        print(f"   Maximum power: {df['Active_Power'].max():.2f} kW")
        print(f"   AC Capacity: {ac_capacity:.2f} kW")
        return
    
    print(f"✅ Clipping window identified:")
    print(f"   Start: {start_idx.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   Stop:  {stop_idx.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   Duration: {(stop_idx - start_idx).total_seconds() / 60:.0f} minutes")
    
    # STEP 2: Calculate Reference PR
    print("\n" + "=" * 80)
    print("📊 STEP 2: Calculating Reference PR")
    print("=" * 80)
    
    reference_pr, pr_details = calculate_reference_pr(
        df, start_idx, stop_idx, dc_capacity, 
        num_points=10, pr_min=0.50, pr_max=0.90
    )
    
    if reference_pr is None:
        print("❌ Could not calculate Reference PR (insufficient clean data)")
        return
    
    print(f"✅ Reference PR calculated: {reference_pr:.4f} ({reference_pr*100:.2f}%)")
    print(f"   Based on {len(pr_details)} clean data points")
    print(f"\n   Sample PR values:")
    for phase, idx, power, poa, pr in pr_details[:5]:
        print(f"      {phase} - {idx.strftime('%H:%M')}: PR = {pr:.4f} "
              f"(Power={power:.0f} kW, POA={poa:.0f} W/m²)")
    
    # STEP 3: Simulate Expected Power
    print("\n" + "=" * 80)
    print("🧮 STEP 3: Simulating Expected Power (Without Clipping)")
    print("=" * 80)
    
    df = simulate_expected_power(
        df, start_idx, stop_idx, reference_pr, dc_capacity, ac_capacity, dc_cap_limit=0.95
    )
    
    print(f"✅ Simulated power calculated for clipping window")
    
    # Show some examples
    start_pos = df.index.get_loc(start_idx)
    sample_indices = [start_pos, start_pos + 15, start_pos + 30]
    
    print(f"\n   Sample calculations:")
    for pos in sample_indices:
        if pos < len(df):
            idx = df.index[pos]
            actual = df.loc[idx, 'Active_Power']
            simulated = df.loc[idx, 'Simulated_Power']
            poa = df.loc[idx, 'POA']
            loss = simulated - actual
            
            print(f"      {idx.strftime('%H:%M')}: POA={poa:>6.0f} W/m² → "
                  f"Simulated={simulated:>7.2f} kW, Actual={actual:>7.2f} kW, "
                  f"Loss={loss:>6.2f} kW")
    
    # STEP 4: Calculate Loss
    print("\n" + "=" * 80)
    print("💰 STEP 4: Calculating Clipping Loss")
    print("=" * 80)
    
    results, df = calculate_clipping_loss(df, start_idx, stop_idx)
    
    print(f"✅ Clipping loss calculated!")
    print(f"\n📋 RESULTS:")
    print(f"   {'Daily Actual Energy':<30}: {results['daily_actual_energy_kwh']:>12,.2f} kWh")
    print(f"   {'Daily Simulated Energy':<30}: {results['daily_simulated_energy_kwh']:>12,.2f} kWh")
    print(f"   {'Clipping Loss Energy':<30}: {results['clipping_loss_energy_kwh']:>12,.2f} kWh")
    print(f"   {'Loss % (vs Actual)':<30}: {results['loss_pct_vs_actual']:>14.2f} %")
    print(f"   {'Loss % (vs Simulated)':<30}: {results['loss_pct_vs_simulated']:>14.2f} %")
    print(f"   {'Peak Clipping Loss':<30}: {results['peak_loss_kw']:>14.2f} kW")
    print(f"   {'Peak Loss Time':<30}: {results['peak_loss_time'].strftime('%H:%M:%S')}")
    print(f"   {'Clipping Duration':<30}: {results['clipping_duration_hours']:>14.2f} hrs")
    
    # Create hourly summary
    clipping_hourly = results['clipping_window_df'].copy()
    clipping_hourly['Hour'] = clipping_hourly.index.hour
    hourly_summary = clipping_hourly.groupby('Hour').agg({
        'Active_Power': 'mean',
        'Simulated_Power': 'mean',
        'Power_Loss_kW': ['sum', 'mean', 'max'],
        'POA': 'mean'
    }).round(2)
    
    hourly_summary.columns = ['Avg_Actual_Power_kW', 'Avg_Simulated_Power_kW', 
                              'Total_Loss_kW', 'Avg_Loss_kW', 'Max_Loss_kW', 'Avg_POA']
    hourly_summary['Energy_Loss_kWh'] = (hourly_summary['Total_Loss_kW'] / 60).round(2)
    
    # Save results to Excel
    base_name = os.path.splitext(excel_file)[0]
    output_file = f"{base_name}_ADVANCED_RESULTS.xlsx"
    
    print(f"\n💾 Saving results to: {output_file}")
    
    with pd.ExcelWriter(output_file, engine='xlsxwriter') as writer:
        # Summary sheet
        summary_data = {
            'Metric': [
                'Analysis Date',
                'Analysis Time Range',
                '',
                'System Parameters',
                'AC Capacity (kW)',
                'DC Capacity (kW)',
                'DC/AC Ratio',
                '',
                'Clipping Window',
                'Clipping Start Time',
                'Clipping Stop Time',
                'Clipping Duration (hours)',
                '',
                'Performance Ratio',
                'Reference PR',
                'Reference PR %',
                '',
                'Energy Analysis',
                'Daily Actual Energy (kWh)',
                'Daily Simulated Energy (kWh)',
                'Clipping Loss Energy (kWh)',
                'Loss % (vs Actual Energy)',
                'Loss % (vs Simulated Energy)',
                '',
                'Peak Clipping',
                'Peak Loss Power (kW)',
                'Peak Loss Time',
            ],
            'Value': [
                df.index[0].strftime('%Y-%m-%d'),
                f"{df.index[0].strftime('%H:%M')} - {df.index[-1].strftime('%H:%M')}",
                '',
                '',
                f"{ac_capacity:.2f}",
                f"{dc_capacity:.2f}",
                f"{dc_ac_ratio:.2f}",
                '',
                '',
                results['clipping_start_time'].strftime('%Y-%m-%d %H:%M:%S'),
                results['clipping_stop_time'].strftime('%Y-%m-%d %H:%M:%S'),
                f"{results['clipping_duration_hours']:.2f}",
                '',
                '',
                f"{reference_pr:.4f}",
                f"{reference_pr*100:.2f}%",
                '',
                '',
                f"{results['daily_actual_energy_kwh']:.2f}",
                f"{results['daily_simulated_energy_kwh']:.2f}",
                f"{results['clipping_loss_energy_kwh']:.2f}",
                f"{results['loss_pct_vs_actual']:.2f}%",
                f"{results['loss_pct_vs_simulated']:.2f}%",
                '',
                '',
                f"{results['peak_loss_kw']:.2f}",
                results['peak_loss_time'].strftime('%H:%M:%S'),
            ]
        }
        
        summary_df = pd.DataFrame(summary_data)
        summary_df.to_excel(writer, sheet_name='Summary', index=False)
        
        # Detailed clipping events
        clipping_events_df = results['clipping_window_df'][['Active_Power', 'Simulated_Power', 'POA', 'Power_Loss_kW']].copy()
        clipping_events_df.columns = ['Actual_Power_kW', 'Simulated_Power_kW', 'POA_Irradiance', 'Power_Loss_kW']
        clipping_events_df['Energy_Loss_kWh'] = (clipping_events_df['Power_Loss_kW'] / 60).round(4)
        clipping_events_df.to_excel(writer, sheet_name='Clipping_Events')
        
        # Hourly summary
        hourly_summary.to_excel(writer, sheet_name='Hourly_Summary')
        
        # PR calculation details
        pr_details_df = pd.DataFrame(pr_details, columns=['Phase', 'Time', 'Power_kW', 'POA', 'PR'])
        pr_details_df.to_excel(writer, sheet_name='PR_Calculation_Details', index=False)
        
        # Full data with simulated power
        full_data_df = df[['Active_Power', 'Simulated_Power', 'POA']].copy()
        full_data_df.columns = ['Actual_Power_kW', 'Simulated_Power_kW', 'POA_Irradiance']
        full_data_df.to_excel(writer, sheet_name='Full_Data')
    
    print("✅ Results saved successfully!")
    print(f"\n📊 Excel file contains {5} sheets:")
    print("   1. Summary - Overall metrics")
    print("   2. Clipping_Events - Minute-by-minute clipping data")
    print("   3. Hourly_Summary - Hourly breakdown of losses")
    print("   4. PR_Calculation_Details - How Reference PR was calculated")
    print("   5. Full_Data - Complete dataset with simulated power")
    
    print("\n" + "=" * 80)
    print("✅ ANALYSIS COMPLETE!")
    print("=" * 80)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python advanced_clipping_calculator.py <excel_file> [filter_date] [hour_start hour_end]")
        print("\nExamples:")
        print("  python advanced_clipping_calculator.py data.xlsx")
        print("  python advanced_clipping_calculator.py data.xlsx 2025-12-26")
        print("  python advanced_clipping_calculator.py data.xlsx 2025-12-26 11 15")
        sys.exit(1)
    
    excel_file = sys.argv[1]
    filter_date = sys.argv[2] if len(sys.argv) > 2 else None
    hour_start = int(sys.argv[3]) if len(sys.argv) > 4 else None
    hour_end = int(sys.argv[4]) if len(sys.argv) > 4 else None
    
    analyze_clipping_advanced(excel_file, filter_date, hour_start, hour_end)

