# 🚀 Advanced Clipping Loss Calculator - User Guide

## 📋 Overview

This script implements the **industry-standard Forced PPC methodology** to automatically calculate solar clipping losses using a scientific 4-step algorithm.

---

## 🎯 What It Does

### **The 4-Step Algorithm:**

1. **🔍 Find the "Clipping Window"**
   - Automatically scans your data to find when the inverter hits AC capacity
   - Identifies START and STOP points of clipping

2. **📊 Calculate "Reference PR" (Performance Ratio)**
   - Takes 20 data points BEFORE clipping starts (when system is normal)
   - Takes 20 data points AFTER clipping ends (when system is normal)
   - Formula: `PR = Actual_Power / (POA × DC_Capacity)`
   - Averages all 20 points to get a "Reference PR"
   - **This tells us:** "When NOT clipping, the system operates at X% efficiency"

3. **🧮 Simulate "What Should Have Been"**
   - For EVERY minute during clipping window
   - Formula: `Simulated_Power = Reference_PR × DC_Capacity × POA`
   - This is what the inverter WOULD have produced without the AC capacity limit

4. **💰 Calculate the Loss**
   - Formula: `Clipping_Loss = Simulated_Energy - Actual_Energy`
   - Minute by minute comparison
   - Sum all minutes and convert to kWh

---

## 📊 Example Output

### **What You'll Get:**

**System Parameters:**
- AC Capacity (from your data)
- DC Capacity (from your data)
- DC/AC Ratio (calculated)

**Clipping Window:**
- Start Time (automatically detected)
- Stop Time (automatically detected)
- Duration in hours and minutes

**Performance Ratio:**
- Reference PR (calculated from clean periods)
- Number of data points used

**Energy Analysis:**
| Metric | Description |
|--------|-------------|
| **Daily Actual Energy** | Total energy actually produced |
| **Daily Simulated Energy** | Energy that could have been produced |
| **Clipping Loss Energy** | Energy lost due to clipping |
| **Loss % (vs Actual)** | Loss as % of actual production |
| **Loss % (vs Simulated)** | Loss as % of potential production |

**Peak Clipping:**
- Peak Loss Power (maximum kW lost at any moment)
- Peak Loss Time (when maximum loss occurred)

> **Note:** Your actual results will be in the Excel output file with your specific values!

---

## 📂 Output Files

The script creates an Excel file named: `[your_input_file]_ADVANCED_RESULTS.xlsx`

It contains **5 comprehensive sheets:**

### **1. Summary Sheet**
Complete overview with:
- System parameters (AC/DC capacity, DC/AC ratio)
- Clipping window timing
- Reference PR calculation
- Energy analysis (Actual, Simulated, Loss)
- Peak clipping metrics

### **2. Clipping_Events Sheet**
Minute-by-minute breakdown during clipping window:
- Actual Power (kW)
- Simulated Power (kW)
- POA Irradiance (W/m²)
- Power Loss (kW) per minute
- Energy Loss (kWh) per minute

### **3. Hourly_Summary Sheet**
Hourly aggregation of clipping losses:
- Average Actual Power
- Average Simulated Power
- Total Loss per hour
- Average Loss per hour
- Max Loss per hour
- Energy Loss (kWh) per hour

### **4. PR_Calculation_Details Sheet**
Shows exactly how Reference PR was calculated:
- Which data points were used (BEFORE/AFTER clipping)
- Time stamps
- Power values
- POA values
- Individual PR calculations
- **Transparency & Auditability**

### **5. Full_Data Sheet**
Complete dataset with simulated power added:
- Every minute of the day
- Actual Power
- Simulated Power
- POA Irradiance

---

## 🖥️ How to Use

### **Basic Usage (Full Day Analysis):**
```bash
python3 advanced_clipping_calculator.py "your_file.xlsx"
```

### **Filter by Date:**
```bash
python3 advanced_clipping_calculator.py "your_file.xlsx" 2025-12-26
```

### **Filter by Time Range (e.g., 11 AM to 3 PM):**
```bash
python3 advanced_clipping_calculator.py "your_file.xlsx" 2025-12-26 11 15
```

### **Examples:**
```bash
# Analyze full day
python3 advanced_clipping_calculator.py "solar_data.xlsx"

# Analyze specific date
python3 advanced_clipping_calculator.py "solar_data.xlsx" 2025-12-26

# Analyze 12 PM to 2 PM only
python3 advanced_clipping_calculator.py "solar_data.xlsx" 2025-12-26 12 14

# Analyze 11 AM to 3 PM only
python3 advanced_clipping_calculator.py "solar_data.xlsx" 2025-12-26 11 15
```

---

## 📋 Required Data Columns

Your Excel file must contain these columns (names can vary slightly):

| Required Column | Variations Recognized |
|----------------|----------------------|
| **DateTime** | DateTime, Date Time |
| **Active Power** | Active Power (kW), Active_Power |
| **POA Irradiance** | POA Irradiance, POA, POA Irradiance (W/m²) |
| **AC Capacity** | AC Capacity, AC_Capacity |
| **DC Capacity** | DC Capacity, DC_Capacity |

**Note:** The script automatically detects column names (case-insensitive).

---

## ✅ Advantages Over Manual Calculation

| Aspect | Manual Method | This Script |
|--------|--------------|-------------|
| **Time** | Hours per day | 30 seconds |
| **Accuracy** | Varies | Consistent scientific method |
| **PR Calculation** | Fixed or assumed | Dynamic, from actual data |
| **Validation** | Hard to verify | Fully transparent & auditable |
| **Reporting** | Manual Excel work | 5 comprehensive sheets |
| **Errors** | Human error prone | Zero calculation errors |
| **Scalability** | 1 day at a time | Process months instantly |

---

## 🔬 How It Compares to Your Manual Calculation

### **Your Manual Method:**
- Expected Power: Pre-calculated
- Clipping Loss: Expected - Actual

### **This Script's Method:**
- Expected Power: Calculated using **Reference PR from clean periods**
- Clipping Loss: Simulated - Actual (scientific methodology)

### **Key Insight:**
If your "Expected Power" is calculated using a similar PR-based formula, then **this script gives you the SAME results but AUTOMATICALLY**!

---

## 📊 Example Console Output

When you run the script, you'll see:

```
================================================================================
🚀 ADVANCED CLIPPING LOSS CALCULATOR - FORCED PPC METHODOLOGY
================================================================================

📂 Reading file: your_file.xlsx
   Loaded XXX rows

📊 System Parameters:
   AC Capacity: X,XXX.XX kW
   DC Capacity: X,XXX.XX kW
   DC/AC Ratio: X.XX

================================================================================
🔍 STEP 1: Finding Clipping Window
================================================================================
✅ Clipping window identified:
   Start: YYYY-MM-DD HH:MM:SS
   Stop:  YYYY-MM-DD HH:MM:SS
   Duration: XXX minutes

================================================================================
📊 STEP 2: Calculating Reference PR
================================================================================
✅ Reference PR calculated: X.XXXX (XX.XX%)
   Based on 20 clean data points

================================================================================
🧮 STEP 3: Simulating Expected Power (Without Clipping)
================================================================================
✅ Simulated power calculated for clipping window

================================================================================
💰 STEP 4: Calculating Clipping Loss
================================================================================
✅ Clipping loss calculated!

📋 RESULTS:
   Daily Actual Energy           :    XX,XXX.XX kWh
   Daily Simulated Energy        :    XX,XXX.XX kWh
   Clipping Loss Energy          :     X,XXX.XX kWh
   Loss % (vs Actual)            :           X.XX %
   Loss % (vs Simulated)         :           X.XX %
   Peak Clipping Loss            :         XXX.XX kW
   Peak Loss Time                : HH:MM:SS
   Clipping Duration             :           X.XX hrs

💾 Saving results to: your_file_ADVANCED_RESULTS.xlsx
✅ Results saved successfully!
```

---

## 🎯 Workflow

### **For Daily Analysis:**

1. **Prepare your data file** (Excel with required columns)
2. **Run the script:**
   ```bash
   python3 advanced_clipping_calculator.py "your_file.xlsx"
   ```
3. **Check the output Excel file** with 5 detailed sheets
4. **Review the Summary sheet** for quick metrics
5. **Check Clipping_Events** for minute-by-minute details
6. **Verify PR_Calculation_Details** for transparency

### **For Monthly Reports:**

Run the script for each day's data:
```bash
python3 advanced_clipping_calculator.py "day1.xlsx"
python3 advanced_clipping_calculator.py "day2.xlsx"
python3 advanced_clipping_calculator.py "day3.xlsx"
...
```

Each will generate its own results file!

---

## ❓ FAQ

### **Q: Why is my Reference PR different from my manual PR?**
A: The script calculates PR dynamically from actual clean (non-clipping) periods on that specific day. Your manual method might use a fixed PR or monthly average.

### **Q: Can I adjust the PR calculation settings?**
A: Yes! In the script, you can modify:
- `num_points=10` (number of points to sample before/after)
- `pr_min=0.50` (minimum acceptable PR)
- `pr_max=0.90` (maximum acceptable PR)

### **Q: What if there's no clipping?**
A: The script will detect no clipping and report it:
```
✅ No clipping detected! System operating below AC capacity.
```

### **Q: Can I use this for multiple inverters?**
A: Currently, the script analyzes single-inverter systems. For multi-inverter analysis, you would need to run it separately for each inverter or modify the script.

### **Q: What if my column names are different?**
A: The script automatically detects common variations. If it can't find your columns, it will tell you which columns are missing.

---

## 🔧 Troubleshooting

**Issue:** "Missing required columns!"
- **Solution:** Check that your Excel has DateTime, Active Power, POA, AC Capacity, DC Capacity columns

**Issue:** "No data after applying filters!"
- **Solution:** Check your date/time filter parameters

**Issue:** "No clipping detected"
- **Solution:** This means your system didn't reach AC capacity - no clipping occurred!

---

## 💡 Tips

1. **Check the PR_Calculation_Details sheet** to see exactly which data points were used
2. **Compare Simulated vs Actual in Full_Data sheet** to visualize clipping
3. **Use time filters** to focus on peak solar hours (11 AM - 3 PM)
4. **Save output files with meaningful names** for tracking over time

---

## 🎉 Success!

You now have a **fully automated, scientific, auditable clipping loss calculator** that implements the industry-standard Forced PPC methodology!

**No more manual calculations needed!** 🚀

---

## 📞 Quick Reference

**Basic Command:**
```bash
python3 advanced_clipping_calculator.py "your_file.xlsx"
```

**Output File:**
```
your_file_ADVANCED_RESULTS.xlsx (5 sheets)
```

**What You Get:**
- Automated clipping detection
- Scientific PR calculation
- Minute-by-minute analysis
- Comprehensive reports
- Full transparency
