#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
处理结果验证工具
用于验证Excel数据解析的准确性和完整性
"""

import pandas as pd
import sys
from pathlib import Path

def validate_medical_records(file_path):
    """
    验证医疗病例解析结果
    
    Args:
        file_path: 处理后的Excel文件路径
    """
    print("=" * 80)
    print("Excel数据解析结果验证工具")
    print("=" * 80)
    
    # 读取文件
    try:
        df = pd.read_excel(file_path)
        print(f"\n✓ 成功读取文件: {file_path}")
        print(f"  总记录数: {len(df)}")
        print(f"  总字段数: {len(df.columns)}")
    except Exception as e:
        print(f"\n✗ 读取文件失败: {e}")
        return
    
    print("\n" + "=" * 80)
    print("1. 字段完整性检查")
    print("=" * 80)
    
    # 期望的字段
    expected_fields = [
        '病例编号', '病例记录', '患者姓名', '性别', '年龄', '就诊日期',
        '主诉症状', '症状持续天数', '既往病史', '体温', '收缩压', '舒张压', 
        '心率', '处方用药'
    ]
    
    # 检查字段是否存在
    missing_fields = [f for f in expected_fields if f not in df.columns]
    extra_fields = [f for f in df.columns if f not in expected_fields]
    
    if not missing_fields:
        print("✓ 所有期望字段都存在")
    else:
        print(f"✗ 缺失字段: {', '.join(missing_fields)}")
    
    if extra_fields:
        print(f"ℹ 额外字段: {', '.join(extra_fields)}")
    
    print("\n" + "=" * 80)
    print("2. 数据完整性检查")
    print("=" * 80)
    
    # 检查每个字段的缺失情况
    for field in expected_fields:
        if field in df.columns:
            null_count = df[field].isna().sum()
            empty_count = (df[field] == '').sum()
            total_missing = null_count + empty_count
            missing_rate = (total_missing / len(df)) * 100
            
            status = "✓" if missing_rate < 5 else "⚠" if missing_rate < 10 else "✗"
            print(f"{status} {field:12} - 缺失: {total_missing:3}/{len(df)} ({missing_rate:5.1f}%)")
    
    print("\n" + "=" * 80)
    print("3. 数据格式验证")
    print("=" * 80)
    
    validation_results = []
    
    # 性别验证
    if '性别' in df.columns:
        valid_genders = df['性别'].isin(['男', '女'])
        invalid_count = (~valid_genders & df['性别'].notna()).sum()
        status = "✓" if invalid_count == 0 else "✗"
        print(f"{status} 性别字段 - 无效值: {invalid_count}/{len(df)}")
        validation_results.append(('性别', invalid_count == 0))
    
    # 年龄验证
    if '年龄' in df.columns:
        try:
            ages = pd.to_numeric(df['年龄'], errors='coerce')
            valid_ages = (ages >= 0) & (ages <= 150)
            invalid_count = (~valid_ages & ages.notna()).sum()
            status = "✓" if invalid_count == 0 else "✗"
            print(f"{status} 年龄字段 - 无效值: {invalid_count}/{len(df)} (有效范围: 0-150)")
            if invalid_count == 0 and ages.notna().sum() > 0:
                print(f"   年龄范围: {ages.min():.0f} - {ages.max():.0f} 岁")
            validation_results.append(('年龄', invalid_count == 0))
        except:
            print("✗ 年龄字段 - 格式错误")
            validation_results.append(('年龄', False))
    
    # 体温验证
    if '体温' in df.columns:
        try:
            temps = pd.to_numeric(df['体温'], errors='coerce')
            valid_temps = (temps >= 35.0) & (temps <= 42.0)
            invalid_count = (~valid_temps & temps.notna()).sum()
            status = "✓" if invalid_count == 0 else "✗"
            print(f"{status} 体温字段 - 无效值: {invalid_count}/{len(df)} (有效范围: 35.0-42.0℃)")
            if invalid_count == 0 and temps.notna().sum() > 0:
                print(f"   体温范围: {temps.min():.1f} - {temps.max():.1f} ℃")
            validation_results.append(('体温', invalid_count == 0))
        except:
            print("✗ 体温字段 - 格式错误")
            validation_results.append(('体温', False))
    
    # 收缩压验证
    if '收缩压' in df.columns:
        try:
            systolic = pd.to_numeric(df['收缩压'], errors='coerce')
            valid_systolic = (systolic >= 60) & (systolic <= 250)
            invalid_count = (~valid_systolic & systolic.notna()).sum()
            status = "✓" if invalid_count == 0 else "✗"
            print(f"{status} 收缩压字段 - 无效值: {invalid_count}/{len(df)} (有效范围: 60-250 mmHg)")
            if invalid_count == 0 and systolic.notna().sum() > 0:
                print(f"   收缩压范围: {systolic.min():.0f} - {systolic.max():.0f} mmHg")
            validation_results.append(('收缩压', invalid_count == 0))
        except:
            print("✗ 收缩压字段 - 格式错误")
            validation_results.append(('收缩压', False))
    
    # 舒张压验证
    if '舒张压' in df.columns:
        try:
            diastolic = pd.to_numeric(df['舒张压'], errors='coerce')
            valid_diastolic = (diastolic >= 40) & (diastolic <= 150)
            invalid_count = (~valid_diastolic & diastolic.notna()).sum()
            status = "✓" if invalid_count == 0 else "✗"
            print(f"{status} 舒张压字段 - 无效值: {invalid_count}/{len(df)} (有效范围: 40-150 mmHg)")
            if invalid_count == 0 and diastolic.notna().sum() > 0:
                print(f"   舒张压范围: {diastolic.min():.0f} - {diastolic.max():.0f} mmHg")
            validation_results.append(('舒张压', invalid_count == 0))
        except:
            print("✗ 舒张压字段 - 格式错误")
            validation_results.append(('舒张压', False))
    
    # 心率验证
    if '心率' in df.columns:
        try:
            heart_rates = pd.to_numeric(df['心率'], errors='coerce')
            valid_hr = (heart_rates >= 40) & (heart_rates <= 200)
            invalid_count = (~valid_hr & heart_rates.notna()).sum()
            status = "✓" if invalid_count == 0 else "✗"
            print(f"{status} 心率字段 - 无效值: {invalid_count}/{len(df)} (有效范围: 40-200 次/分)")
            if invalid_count == 0 and heart_rates.notna().sum() > 0:
                print(f"   心率范围: {heart_rates.min():.0f} - {heart_rates.max():.0f} 次/分")
            validation_results.append(('心率', invalid_count == 0))
        except:
            print("✗ 心率字段 - 格式错误")
            validation_results.append(('心率', False))
    
    print("\n" + "=" * 80)
    print("4. 数据质量统计")
    print("=" * 80)
    
    # 计算整体准确率
    passed_validations = sum([1 for _, result in validation_results if result])
    total_validations = len(validation_results)
    accuracy = (passed_validations / total_validations * 100) if total_validations > 0 else 0
    
    print(f"字段格式验证通过率: {passed_validations}/{total_validations} ({accuracy:.1f}%)")
    
    # 计算数据完整率
    completeness_rates = []
    for field in expected_fields:
        if field in df.columns:
            null_count = df[field].isna().sum()
            empty_count = (df[field] == '').sum()
            complete_rate = (len(df) - null_count - empty_count) / len(df) * 100
            completeness_rates.append(complete_rate)
    
    avg_completeness = sum(completeness_rates) / len(completeness_rates) if completeness_rates else 0
    print(f"平均数据完整率: {avg_completeness:.1f}%")
    
    print("\n" + "=" * 80)
    print("5. 数据示例展示（前3条）")
    print("=" * 80)
    
    # 显示前3条数据的关键字段
    key_fields = ['病例编号', '患者姓名', '性别', '年龄', '体温', '收缩压', '舒张压', '心率']
    display_fields = [f for f in key_fields if f in df.columns]
    
    for idx, row in df.head(3).iterrows():
        print(f"\n【记录 {idx + 1}】")
        for field in display_fields:
            print(f"  {field}: {row[field]}")
    
    print("\n" + "=" * 80)
    print("6. 验证总结")
    print("=" * 80)
    
    # 综合评估
    overall_pass = accuracy >= 90 and avg_completeness >= 95
    
    if overall_pass:
        print("✓ 数据质量良好，可以用于后续分析")
    else:
        print("⚠ 数据质量需要改进")
        if accuracy < 90:
            print(f"  - 格式验证通过率较低 ({accuracy:.1f}%)，建议优化提示词")
        if avg_completeness < 95:
            print(f"  - 数据完整率较低 ({avg_completeness:.1f}%)，建议检查规则配置")
    
    print("\n建议：")
    print("  1. 随机抽取5-10条记录进行人工核对")
    print("  2. 对比原始数据和提取结果，确认准确性")
    print("  3. 如发现问题，调整提示词后重新处理")
    
    print("\n" + "=" * 80)

def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("使用方法: python validate_results.py <excel_file_path>")
        print("\n示例:")
        print("  python validate_results.py excel_parser_data/exports/processed_xxx.xlsx")
        return
    
    file_path = sys.argv[1]
    
    if not Path(file_path).exists():
        print(f"错误: 文件不存在 - {file_path}")
        return
    
    validate_medical_records(file_path)

if __name__ == "__main__":
    main()

