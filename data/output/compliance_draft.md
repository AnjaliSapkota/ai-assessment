# SunBridge Trading — Import Compliance Draft

## 1. Executive summary

This report provides a professional draft import-document assessment for the target product SUN-5K-G06P3, based on a structured reconciliation of two manufacturer datasheets (Source 1 and Source 2).

Source 1 and Source 2 show substantial agreement on several core parameters, but substantive discrepancies and source-specific information require clarification.

Major agreements include:
- Core DC input parameters (Max. DC Input Power of 6.5 kW, Max. DC Input Voltage of 1100 V, Start-up Voltage of 140 V, and MPPT Operating Range of 120-1000 V).
- Core AC output parameters (Rated Output Power of 5 kW, Rated AC Grid Output Current of 7.6/7.3 A, and Max. AC Output Current of 8.4/8 A).
- Physical dimensions (283×463×178 mm), weight (11 kg), and safety/EMC standards (IEC/EN 61000-6-1/2/3/4, IEC/EN 62109-1, IEC/EN 62109-2).
- Numerous protection features (DC Reverse-Polarity, AC Short Circuit, AC Output Overcurrent, Output Overvoltage, Insulation Resistance, Ground Fault, Anti-islanding, and Temperature Protection).

Major substantive conflicts include:
- Max. Active / Apparent Power: Source 1 lists "5.5 kW" (active power), whereas Source 2 lists "5.5 kVA" (apparent power).
- Euro Efficiency: Source 1 lists "97.5%" while Source 2 lists "97.6%".
- Inverter Topology: Source 1 lists "Transformerless" while Source 2 lists "Non-Isolated".
- Grid Connection Standards/Regulations: Source 1 lists "IEC 61727, IEC 62116, EN 50549", whereas Source 2 lists "OVE-Richtlinie R25, G99, VDE-AR-N 4105".

Important missing or uncertain information:
- Max. DC Input Current, Max. Short Circuit Current, and Number of Strings per MPP Tracker are not established in either source for the target model.
- Source 2 contains corrupted fields, specifically a corrupted "Type of Cooling" field that appends grid standards to the cooling type, and a corrupted field labeled "GWeenigehrat l( kDga)ta" with a value of "4.8".

Manufacturer clarification is required to resolve these technical conflicts, address missing values, and clarify corrupted fields before proceeding with import decisions. This document is an AI-assisted draft for review and is not a final legal, customs, engineering, or regulatory determination.

## 2. Product identification

- Model: SUN-5K-G06P3
- Product type: Not established from the supplied documents.
- Manufacturer: Ningbo Deye Inverter Technology Co., Ltd.

## 3. Manufacturer / document observations

Both Source 1 and Source 2 are datasheets from Ningbo Deye Inverter Technology Co., Ltd. covering eight models: SUN-4K-G06P3, SUN-5K-G06P3, SUN-6K-G06P3, SUN-7K-G06P3, SUN-8K-G06P3, SUN-10K-G06P3, SUN-12K-G06P3, and SUN-15K-G06P3.

Source 1 is identified as "Ningbo Deye Inverter Technology Co., Ltd. Datasheet (Source 1)" and Source 2 is identified as "Ningbo Deye Inverter Technology Co., Ltd. Datasheet (Source 2)".

Source 1 contains several unique fields not present in Source 2, such as "No. of MPP Trackers", "Display", "Internal Consumption", "Integrated DC Switch", "Remote Software Upload", and "Remote Change of Operating Parameters".

Source 2 contains unique fields such as "Rated PV Input Voltage", "Over Voltage Category", and several specific monitoring/protection functions (DC Component Monitoring, Power Network Monitoring, Earth Fault Detection, Overvoltage Load Drop Protection, and Residual Current (RCD) Detection).

Source 2 exhibits significant extraction and corruption issues, notably a corrupted "Type of Cooling" field that appends a list of grid standards to the cooling type, and a corrupted field labeled "GWeenigehrat l( kDga)ta" with a value of "4.8" across all models.

Model-specific missing values for the target model SUN-5K-G06P3 include Max. DC Input Current, Max. Short Circuit Current, and Number of Strings per MPP Tracker, which are null in both sources. Additionally, Source 2 has a null value for the number of MPP trackers for this model.

## 4. Technical specifications for SUN-5K-G06P3

| Parameter | Source 1 | Source 2 | Status |
|---|---|---|---|
| Max. DC Input Power | 6.5 kW | 6.5 kW | agreement |
| Max. DC Input Voltage | 1100 V | 1100 V | agreement |
| Start-up DC Input Voltage | 140 V | 140 V | agreement |
| MPPT Operating Range | 120-1000 V | 120-1000 V | agreement |
| Rated PV Input Voltage | Not established from the supplied documents. | 600 V | source_2_only |
| Max. DC Input Current | Not established from the supplied documents. | Not established from the supplied documents. | uncertain |
| Max. Short Circuit Current | Not established from the supplied documents. | Not established from the supplied documents. | uncertain |
| No. of MPP Trackers | 2 | Not established from the supplied documents. | source_1_only |
| No. of Strings per MPP Tracker | Not established from the supplied documents. | Not established from the supplied documents. | uncertain |
| Rated Output Power | 5 kW | 5 kW | agreement |
| Max. Active / Apparent Power | 5.5 kW | 5.5 kVA | conflict |
| Rated Output Voltage/Range | 3L/N/PE 220/380V, 230/400V 0.85Un-1.1Un (this may vary with grid standards) | 220/380V, 230/400V 0.85Un-1.1Un | agreement |
| Operating Phase / Grid Connection Form | Three Phase | 3L/N/PE | agreement |
| Rated AC Grid Output Current | 7.6/7.3 A | 7.6/7.3 A | agreement |
| Max. AC Output Current | 8.4/8 A | 8.4/8 A | agreement |
| Power Factor Adjustment Range | 0.8 leading to 0.8 lagging | 0.8 leading to 0.8 lagging | agreement |
| Total Harmonics Current Distortion (THDi) | <3% | <3% | agreement |
| DC Injection Current | <0.5% | <0.5%ln | agreement |
| Max. Efficiency | 98.2% | 98.2% | agreement |
| Euro Efficiency | 97.5% | 97.6% | conflict |
| MPPT Efficiency | >99% | >99% | agreement |
| Cabinet Size | 283×463×178 (Excluding connectors and brackets) mm | 283×463×178 (Excluding Connectors and Brackets) mm | agreement |
| Weight | 11 kg | 11 kg | agreement |
| Topology | Transformerless | Non-Isolated | conflict |
| Running Temperature | -25 to +60 , >45 Derating ℃ ℃ | -25 to +60 , >45 Derating ℃ ℃ | agreement |
| Ingress Protection | IP65 | IP 65 | agreement |
| Noise Emission | <45 dB | <45 | agreement |
| Cooling Concept | Free Cooling Smart Cooling | Natural Cooling IEC 61727, IEC 62116, CEI 0-21, EN 50549, NRS 097, RD 140, UNE 217002 | uncertain |
| Permissible Altitude | 4000 m | 4000m | agreement |
| Warranty | 5 Years | 5 Years | agreement |
| Grid Connection Standard / Grid Regulation | IEC 61727, IEC 62116, EN 50549 | OVE-Richtlinie R25, G99, VDE-AR-N 4105 | conflict |
| Safety / EMC Standard | IEC/EN 61000-6-1/2/3/4, IEC/EN 62109-1, IEC/EN 62109-2 | IEC/EN 61000-6-1/2/3/4, IEC/EN 62109-1, IEC/EN 62109-2 | agreement |
| Display | LCD1602 | Not established from the supplied documents. | source_1_only |
| Interface | RS485/RS232/Wifi/LAN | RS485/RS232 /WiFi/LAN | agreement |
| Internal Consumption | <1W (Night) | Not established from the supplied documents. | source_1_only |
| Over Voltage Category | Not established from the supplied documents. | OVC II(DC), OVC III(AC) | source_2_only |
| Surge Protection | DC Type II / AC Type II | TYPE II(DC), TYPE II(AC) | agreement |
| DC Reverse-Polarity Protection | Yes | Yes | agreement |
| AC Short Circuit Protection | Yes | Yes | agreement |
| AC Output Overcurrent Protection | Yes | Yes | agreement |
| Output Overvoltage Protection | Yes | Yes | agreement |
| Insulation Resistance Protection | Yes | Yes | agreement |
| Ground Fault Monitoring | Yes | Yes | agreement |
| Anti-islanding Protection | Yes | Yes | agreement |
| Temperature Protection | Yes | Yes | agreement |
| Integrated DC Switch | Yes | Not established from the supplied documents. | source_1_only |
| Remote Software Upload | Yes | Not established from the supplied documents. | source_1_only |
| Remote Change of Operating Parameters | Yes | Not established from the supplied documents. | source_1_only |
| DC Component Monitoring | Not established from the supplied documents. | Yes | source_2_only |
| Power Network Monitoring | Not established from the supplied documents. | Yes | source_2_only |
| Earth Fault Detection | Not established from the supplied documents. | Yes | source_2_only |
| Overvoltage Load Drop Protection | Not established from the supplied documents. | Yes | source_2_only |
| Residual Current (RCD) Detection | Not established from the supplied documents. | Yes | source_2_only |
| GWeenigehrat l( kDga)ta | Not established from the supplied documents. | 4.8 | uncertain |

## 5. Cross-document comparison

### Technical conflicts

- **Max. Active / Apparent Power:** Source 1 lists "5.5 kW" (Max. Active Power), whereas Source 2 lists "5.5 kVA" (Max. AC Output Apparent Power). These represent different physical units and concepts (active vs. apparent power) and must be clarified.
- **Euro Efficiency:** Source 1 lists "97.5%" while Source 2 lists "97.6%".
- **Topology:** Source 1 lists "Transformerless" while Source 2 lists "Non-Isolated". Although these terms are often related in solar inverter design, they are distinct technical terms and represent a terminology conflict.
- **Grid Connection Standard / Grid Regulation:** Source 1 lists "IEC 61727, IEC 62116, EN 50549" under Grid Connection Standard, whereas Source 2 lists "OVE-Richtlinie R25, G99, VDE-AR-N 4105" under Grid Regulation.

### Source-specific information

- **Source 1 Only:**
  - No. of MPP Trackers is listed as "2".
  - Display is listed as "LCD1602".
  - Internal Consumption is listed as "<1W (Night)".
  - Integrated DC Switch is listed as "Yes".
  - Remote Software Upload is listed as "Yes".
  - Remote Change of Operating Parameters is listed as "Yes".
- **Source 2 Only:**
  - Rated PV Input Voltage is listed as "600 V".
  - Over Voltage Category is listed as "OVC II(DC), OVC III(AC)".
  - DC Component Monitoring is listed as "Yes".
  - Power Network Monitoring is listed as "Yes".
  - Earth Fault Detection is listed as "Yes".
  - Overvoltage Load Drop Protection is listed as "Yes".
  - Residual Current (RCD) Detection is listed as "Yes".

### Missing or uncertain information

- **Max. DC Input Current:** This parameter is null in both sources for the SUN-5K-G06P3 model.
- **Max. Short Circuit Current:** This parameter is null in both sources for the SUN-5K-G06P3 model.
- **No. of Strings per MPP Tracker:** This parameter is null in both sources for the SUN-5K-G06P3 model.
- **Cooling Concept:** Source 1 lists "Free Cooling Smart Cooling". Source 2 lists "Natural Cooling IEC 61727, IEC 62116, CEI 0-21, EN 50549, NRS 097, RD 140, UNE 217002", which is corrupted and appends grid standards to the cooling type.
- **GWeenigehrat l( kDga)ta:** This field is corrupted in Source 2 with a value of "4.8" and is not present in Source 1.

### Presentation differences

- **Rated Output Voltage/Range:** Source 1 includes "3L/N/PE" and "(this may vary with grid standards)" in the value, whereas Source 2 lists "220/380V, 230/400V 0.85Un-1.1Un".
- **Operating Phase / Grid Connection Form:** Source 1 lists "Three Phase" under "Operating Phase", while Source 2 lists "3L/N/PE" under "Grid Connection Form".
- **DC Injection Current:** Source 1 lists "<0.5%" while Source 2 lists "<0.5%ln".
- **Ingress Protection:** Source 1 lists "IP65" while Source 2 lists "IP 65".
- **Noise Emission:** Source 1 lists "<45 dB" while Source 2 lists "<45".
- **Permissible Altitude:** Source 1 lists "4000 m" while Source 2 lists "4000m".
- **Interface:** Source 1 lists "RS485/RS232/Wifi/LAN" while Source 2 lists "RS485/RS232 /WiFi/LAN".
- **Surge Protection:** Source 1 lists "DC Type II / AC Type II" while Source 2 lists "TYPE II(DC), TYPE II(AC)".
- **Protection Terminology:** Minor differences in naming (e.g., "DC Reverse-Polarity Protection" vs "DC Polarity Reverse Connection Protection", "Insulation Resistance Protection" vs "DC Terminal Insulation Impedance Monitoring", "Ground Fault Monitoring" vs "Ground Fault Current Monitoring", "Anti-islanding Protection" vs "Island Protection Monitoring", "Temperature Protection" vs "Thermal Protection"). These are presentation/naming differences and do not represent substantive conflicts.

## 6. Testing and standards evidence

The following standards and regulations are listed in the datasheets:
- **Grid Connection Standards / Regulations (Source 1):** IEC 61727, IEC 62116, EN 50549
- **Grid Connection Standards / Regulations (Source 2):** OVE-Richtlinie R25, G99, VDE-AR-N 4105 (Note: Source 2 also has a corrupted cooling field that appends: IEC 61727, IEC 62116, CEI 0-21, EN 50549, NRS 097, RD 140, UNE 217002)
- **Safety / EMC Standards (Both Sources):** IEC/EN 61000-6-1/2/3/4, IEC/EN 62109-1, IEC/EN 62109-2

Certification evidence is not established from the supplied documents.

## 7. Labeling / nameplate information

Not established from the supplied documents.

## 8. Uncertainties and extraction issues

- **Missing Values:** Max. DC Input Current (A), Max. Short Circuit Current (A), and No. of Strings per MPP Tracker are null in both sources for SUN-5K-G06P3.
- **Corrupted Labels:**
  - The field "Type of Cooling" in Source 2 is corrupted, merging the cooling type "Natural Cooling" with a list of grid standards ("IEC 61727, IEC 62116, CEI 0-21, EN 50549, NRS 097, RD 140, UNE 217002").
  - The field "GWeenigehrat l( kDga)ta" in Source 2 is corrupted and its meaning is highly uncertain, though its value is "4.8" across all models.
- **Source-Only Fields:** Several fields are present in only one source (e.g., Display, Internal Consumption, Integrated DC Switch, Remote Software Upload, Remote Change of Operating Parameters in Source 1; Rated PV Input Voltage, Over Voltage Category, DC Component Monitoring, Power Network Monitoring, Earth Fault Detection, Overvoltage Load Drop Protection, Residual Current (RCD) Detection in Source 2).

## 9. Items requiring confirmation from manufacturer

1. Resolve the technical conflict regarding maximum output power: Source 1 lists "Max. Active Power" as 5.5 kW, while Source 2 lists "Max. AC Output Apparent Power" as 5.5 kVA. Please confirm the correct active and apparent power ratings.
2. Resolve the conflict in Euro Efficiency: Source 1 lists 97.5% while Source 2 lists 97.6%. Please confirm the correct value.
3. Resolve the conflict in Inverter Topology: Source 1 lists "Transformerless" while Source 2 lists "Non-Isolated". Please clarify the exact topology.
4. Clarify the applicable Grid Connection Standards and Regulations, as Source 1 lists "IEC 61727, IEC 62116, EN 50549" and Source 2 lists "OVE-Richtlinie R25, G99, VDE-AR-N 4105".
5. Provide the missing technical specifications for the SUN-5K-G06P3 model: Max. DC Input Current (A), Max. Short Circuit Current (A), and Number of Strings per MPP Tracker.
6. Clarify the correct cooling concept for the SUN-5K-G06P3 model, as Source 1 lists "Free Cooling Smart Cooling" and Source 2 contains a corrupted field merging "Natural Cooling" with grid standards.
7. Clarify the meaning and correct label for the corrupted field "GWeenigehrat l( kDga)ta" (value 4.8) in Source 2.
8. Confirm whether the source-specific features (such as Display, Internal Consumption, Integrated DC Switch, Remote Software Upload, Remote Change of Operating Parameters, Over Voltage Category, and various monitoring functions) are standard or optional for the SUN-5K-G06P3 model.
9. Provide available supporting test reports, certificates, declarations, or other evidence corresponding to the standards or regulations listed in the datasheets, where applicable.

## 10. Short methodology note

This report was prepared by extracting and normalizing technical data from two manufacturer datasheets provided for the SUN-5K-G06P3 model. Gemini was utilized to perform a structured reconciliation of the extracted parameters. No outside knowledge was used, and all missing, conflicting, or corrupted information has been preserved and highlighted. Values from other inverter models in the same product families were not substituted. This document is an AI-assisted draft for review and is not a final legal, customs, engineering, or regulatory determination.