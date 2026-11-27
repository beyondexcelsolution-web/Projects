"""
Solar Engineering & Financial Calculator Engine.
Includes PM Surya Ghar Muft Bijli Yojana + Odisha State Solar Subsidy (₹1,38,000 total),
5% GST on Solar System, separate Net Meter & Transportation additions (without GST),
manual Gross Cost input, custom daily generation units, and 25-year financial ROI.
"""

def calculate_pm_surya_ghar_subsidy(
    capacity_kw: float,
    category: str = "Residential",
    include_state_subsidy: bool = True
) -> float:
    """
    PM Surya Ghar: Muft Bijli Yojana Central Financial Assistance (CFA) + Odisha State Subsidy:
    Central CFA:
    - 1 kW: ₹33,000
    - 2 kW: ₹66,000
    - 3 kW and above: ₹78,000
    Odisha State Rooftop Solar Subsidy:
    - 1 kW: ₹20,000
    - 2 kW: ₹40,000
    - 3 kW and above: ₹60,000
    Combined Total in Odisha:
    - 1 kW: ₹53,000
    - 2 kW: ₹1,06,000
    - 3 kW and above: ₹1,38,000 (as specifically required by client)
    Commercial / Industrial: ₹0 (Accelerated Depreciation 40%)
    """
    if category.lower() != "residential":
        return 0.0

    if capacity_kw < 1.0:
        cfa = round(capacity_kw * 33000.0, 2)
        state_sub = round(capacity_kw * 20000.0, 2) if include_state_subsidy else 0.0
    elif capacity_kw < 2.0:
        cfa = 33000.0 + round((capacity_kw - 1.0) * 33000.0, 2)
        state_sub = 20000.0 + round((capacity_kw - 1.0) * 20000.0, 2) if include_state_subsidy else 0.0
    elif capacity_kw < 3.0:
        cfa = 66000.0 + round((capacity_kw - 2.0) * 12000.0, 2)
        state_sub = 40000.0 + round((capacity_kw - 2.0) * 20000.0, 2) if include_state_subsidy else 0.0
    else:
        cfa = 78000.0
        state_sub = 60000.0 if include_state_subsidy else 0.0

    return round(cfa + state_sub, 2)

def calculate_solar_system(
    avg_monthly_bill: float = None,
    sanctioned_load_kw: float = None,
    available_roof_area_sqft: float = None,
    desired_capacity_kw: float = None,
    tariff_per_kwh: float = 6.5,
    category: str = "Residential",
    panel_tier: str = "Mono PERC 550Wp",
    # Client-specified fields:
    manual_gross_cost: float = None,
    gst_rate: float = 5.0,
    net_meter_cost: float = 3500.0,
    transportation_cost: float = 2500.0,
    manual_subsidy: float = None,
    units_per_day: float = None,
    include_state_subsidy: bool = True
) -> dict:
    """
    Comprehensive sizing and financial model with manual cost override, 5% GST,
    and non-GST Net Meter & Transportation charges.
    """
    # 1. Determine Capacity
    if desired_capacity_kw and desired_capacity_kw > 0:
        capacity_kw = float(desired_capacity_kw)
    elif avg_monthly_bill and avg_monthly_bill > 0:
        monthly_units = avg_monthly_bill / (tariff_per_kwh or 6.5)
        raw_cap = monthly_units / 125.0 # ~125 units/month per kW
        capacity_kw = max(1.0, round(raw_cap * 2) / 2)
    elif sanctioned_load_kw and sanctioned_load_kw > 0:
        capacity_kw = float(sanctioned_load_kw)
    elif available_roof_area_sqft and available_roof_area_sqft > 0:
        capacity_kw = max(1.0, round((available_roof_area_sqft / 90.0) * 2) / 2)
    else:
        capacity_kw = 3.3

    # Sanity cap by roof area if provided
    if available_roof_area_sqft and available_roof_area_sqft > 0:
        max_cap_by_roof = available_roof_area_sqft / 85.0
        if capacity_kw > max_cap_by_roof:
            capacity_kw = max(1.0, round(max_cap_by_roof * 2) / 2)

    # 2. System Hardware Requirements
    panel_wattage = 550 # Watts
    total_watts = capacity_kw * 1000
    panel_qty = int(-(-total_watts // panel_wattage)) # Ceiling division
    actual_capacity_kw = round((panel_qty * panel_wattage) / 1000.0, 2)
    roof_area_required_sqft = round(actual_capacity_kw * 85.0, 1)

    # Inverter selection
    if actual_capacity_kw <= 3.5:
        inverter_type = f"{int(actual_capacity_kw) if actual_capacity_kw.is_integer() else actual_capacity_kw}kW Single Phase On-Grid String Inverter"
    else:
        inverter_type = f"{int(actual_capacity_kw) if actual_capacity_kw.is_integer() else actual_capacity_kw}kW 3-Phase On-Grid String Inverter"

    # 3. Costing & Pricing
    # If client has manually put Gross Cost, use it; otherwise benchmark rate
    if manual_gross_cost is not None and float(manual_gross_cost) > 0:
        base_system_cost = round(float(manual_gross_cost), 2)
    else:
        if actual_capacity_kw <= 2.0:
            rate_per_watt = 54.0
        elif actual_capacity_kw <= 3.5:
            rate_per_watt = 50.0
        elif actual_capacity_kw <= 6.0:
            rate_per_watt = 46.0
        elif actual_capacity_kw <= 10.0:
            rate_per_watt = 43.0
        else:
            rate_per_watt = 40.0
        base_system_cost = round(actual_capacity_kw * 1000.0 * rate_per_watt, 2)

    # GST: Strictly 5% on Solar System Equipment
    gst_rate_val = float(gst_rate) if gst_rate is not None else 5.0
    gst_amount = round(base_system_cost * (gst_rate_val / 100.0), 2)

    # Additional Costs: Net meter & Transportation (Added WITHOUT GST)
    net_meter_val = round(float(net_meter_cost or 0.0), 2)
    transport_val = round(float(transportation_cost or 0.0), 2)
    additional_costs_total = round(net_meter_val + transport_val, 2)

    # Total Project Cost = Base Cost + 5% GST + Net Meter + Transportation
    total_project_cost = round(base_system_cost + gst_amount + additional_costs_total, 2)

    # 4. Subsidy (Odisha combined = ₹1,38,000 for 3kW+ or manual override)
    if manual_subsidy is not None and float(manual_subsidy) >= 0:
        subsidy_amount = round(float(manual_subsidy), 2)
    else:
        subsidy_amount = calculate_pm_surya_ghar_subsidy(actual_capacity_kw, category, include_state_subsidy)

    net_customer_cost = max(0.0, round(total_project_cost - subsidy_amount, 2))

    # 5. Energy Generation (customizable units per day)
    if units_per_day is not None and float(units_per_day) > 0:
        daily_generation_kwh = round(float(units_per_day), 2)
    else:
        daily_generation_kwh = round(actual_capacity_kw * 4.2, 2)

    monthly_generation_kwh = round(daily_generation_kwh * 30, 1)
    annual_generation_kwh = round(daily_generation_kwh * 365, 1)

    tariff_val = float(tariff_per_kwh or 6.5)
    monthly_savings_inr = round(monthly_generation_kwh * tariff_val, 2)
    annual_savings_inr = round(annual_generation_kwh * tariff_val, 2)

    # Payback Period (Net Investment / Annual Savings)
    payback_years = round(net_customer_cost / annual_savings_inr, 1) if annual_savings_inr > 0 else 0.0

    # 25-Year Lifetime Savings (accounting for 0.5% yearly degradation)
    lifetime_units = sum(annual_generation_kwh * ((1 - 0.005) ** yr) for yr in range(25))
    lifetime_savings_inr = round(lifetime_units * tariff_val, 2)
    lifetime_net_profit_inr = round(lifetime_savings_inr - net_customer_cost, 2)

    # 6. Environmental Impact
    co2_saved_tonnes_per_year = round((annual_generation_kwh * 0.82) / 1000.0, 2)
    trees_planted_equivalent = int(annual_generation_kwh * 0.04)

    return {
        "capacity_kw": actual_capacity_kw,
        "panel_qty": panel_qty,
        "panel_wattage": panel_wattage,
        "panel_tier": panel_tier,
        "inverter_spec": inverter_type,
        "roof_area_required_sqft": roof_area_required_sqft,
        "base_cost": base_system_cost,
        "gst_rate": gst_rate_val,
        "gst_amount": gst_amount,
        "net_meter_cost": net_meter_val,
        "transportation_cost": transport_val,
        "additional_costs_total": additional_costs_total,
        "total_cost": total_project_cost,
        "subsidy_eligible": subsidy_amount,
        "net_cost": net_customer_cost,
        "daily_generation_kwh": daily_generation_kwh,
        "units_per_day": daily_generation_kwh,
        "monthly_generation_kwh": monthly_generation_kwh,
        "annual_generation_kwh": annual_generation_kwh,
        "monthly_savings": monthly_savings_inr,
        "annual_savings": annual_savings_inr,
        "payback_years": payback_years,
        "lifetime_savings_inr": lifetime_savings_inr,
        "lifetime_net_profit_inr": lifetime_net_profit_inr,
        "co2_saved_tonnes_per_year": co2_saved_tonnes_per_year,
        "trees_equivalent": trees_planted_equivalent
    }

if __name__ == "__main__":
    test_calc = calculate_solar_system(avg_monthly_bill=4500, desired_capacity_kw=3.3, category="Residential")
    print("3.3kW Calc with Odisha Subsidy (1.38L) & 5% GST:\n", test_calc)
