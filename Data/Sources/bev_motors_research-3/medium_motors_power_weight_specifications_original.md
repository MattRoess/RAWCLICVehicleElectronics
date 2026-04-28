# Research Report: Power and Weight Specifications of Medium Auxiliary Motors in Modern Battery Electric Vehicles

**Report Date: 2026-02-17**

## Executive Summary

This report presents a detailed analysis of the power ratings and weight specifications for medium Direct Current (DC) motors and stepper motors utilized in the auxiliary systems of 2024-2026 European and Asian Battery Electric Vehicle (BEV) models sold in Europe. The primary objective was to document actual component specifications from leading automotive suppliers and to critically evaluate the accuracy of a commonly cited 50-500 Watt (W) power range for this category of motors.

The investigation reveals that the 50-500W classification for "medium motors" is an oversimplification that does not fully capture the diverse landscape of auxiliary motor applications in modern BEVs. The research confirms that this power range is accurate for a specific subset of high-load DC motor applications. For instance, brushless DC motors in Heating, Ventilation, and Air Conditioning (HVAC) blower units and electric coolant pumps for battery and powertrain thermal management demonstrably operate within this range, with some HVAC motors reaching up to 300W and coolant pump motors being classified in segments up to and exceeding 400W. These components are characterized by their continuous or high-demand operation and significant impact on vehicle efficiency and performance.

Conversely, a substantial number of auxiliary systems rely on motors with power ratings significantly below the 50W threshold. Many conventional brushed DC motors used in high-volume applications such as power window regulators and windshield wipers were found to have nominal power ratings between 3W and 15W. Furthermore, the analysis of stepper motors, which are integral to precision control systems like headlight leveling, HVAC blend doors, and active grille shutters, shows that they are fundamentally low-power devices. Their consumption is typically in the low double-digit watt range at maximum, with many operating below 10W.

Weight specifications were found to be highly application-dependent. High-power brushless DC motors, such as those in HVAC systems, can weigh approximately 1 kilogram. In contrast, smaller DC motors for window regulation are in the 0.6 kg range, and compact stepper motors for functions like headlight leveling weigh as little as 90 grams.

In conclusion, while the 50-500W range correctly identifies the power requirements for the most demanding BEV auxiliary functions, it excludes the vast majority of lower-power DC and stepper motor actuators that are ubiquitous in modern vehicles. A more nuanced classification is required, segmenting auxiliary motors by application and technology. The trend is clearly toward highly efficient, intelligent, and networked brushless DC and stepper motors, where control precision and energy conservation are prioritized over raw power output for most comfort, convenience, and safety-related actuations.

## Introduction

The rapid evolution of Battery Electric Vehicles (BEVs) has fundamentally reshaped automotive engineering, placing unprecedented emphasis on electrical system efficiency. Beyond the primary traction motor, a complex ecosystem of auxiliary electric motors performs critical functions that support vehicle operation, passenger comfort, safety, and thermal management. These auxiliary systems, which include everything from HVAC blowers and coolant pumps to power seats and adaptive headlights, represent a significant and continuous load on the vehicle's high-voltage battery. Consequently, understanding the precise power consumption and weight of their constituent motors is paramount for optimizing vehicle range, performance, and overall design.

This report addresses the research objective to investigate and document the actual power and weight specifications of two key motor types—medium DC motors and medium stepper motors—used in the auxiliary systems of contemporary BEVs (2024-2026 European and Asian models). These components are supplied by major Tier 1 automotive manufacturers such as Bosch, Valeo, Continental, Brose, and Nidec, whose products define the technological standards within the industry.

The analysis will proceed in two main sections. The first section will examine DC motors, differentiating between high-power applications like thermal management and lower-power comfort and convenience functions. The second section will focus on stepper motors, which are primarily used for precision control in various mechatronic systems. Throughout the report, specific data points on power ratings (in Watts) and weight (in kilograms or grams) will be presented and analyzed. This evidence-based approach will culminate in a final assessment that critically evaluates the validity of a generalized 50-500W power range for "medium" auxiliary motors, providing a more refined understanding of the power distribution across these essential BEV components.

## Analysis of DC Motors in BEV Auxiliary Systems

DC motors have long been the workhorses of automotive auxiliary systems. In the context of BEVs, their role has become even more critical, with a pronounced technological shift from traditional brushed DC motors towards more efficient, reliable, and controllable Brushless DC (BLDC) motors. This evolution is driven by the relentless need to minimize energy consumption to maximize driving range. The analysis of DC motors can be effectively segmented into two distinct categories based on their power requirements: high-power applications essential for vehicle operation and thermal stability, and lower-power applications related to passenger comfort, convenience, and other actuation tasks.

### High-Power Applications: Thermal Management and HVAC Systems

The most power-intensive auxiliary DC motors in a BEV are those responsible for thermal management. This includes circulating air within the cabin via the HVAC system and circulating liquid coolant to regulate the temperature of the battery pack, traction motor, and power electronics. These functions are not optional; they are fundamental to the vehicle's performance, safety, and longevity.

Research into components from Valeo, a leading supplier of thermal systems, provides a clear example for HVAC systems. Valeo's advanced brushless HVAC blower motors are specifically highlighted for their suitability in BEVs, primarily due to their high efficiency, which approaches 80%. These motors are designed to operate across a wide power spectrum, with specifications indicating a mechanical power output of up to 300W. The weight of a typical brushless blower motor assembly, including the impeller wheel, is approximately 1 kilogram. The significant power requirement is necessary to move large volumes of air for effective cabin heating and cooling, while the high efficiency ensures this is achieved with minimal impact on the vehicle's battery reserves. These motors often feature integrated power modules and support communication via LIN or PWM protocols, allowing for precise speed control by the vehicle's climate control unit.

Similarly, the electric pumps that circulate coolant are vital. Data concerning the electric coolant pump market, in which Continental AG is a major player, reveals a clear power segmentation. While specific motor specifications are proprietary, the market is categorized by power ratings, including segments for 50-100W, 100-400W, and even greater than 400W. These electric pumps operate independently of the main traction motor and are essential for tasks such as cooling the battery during fast charging or managing the temperature of the power inverter under heavy load. The existence of these high-power categories confirms that motors for BEV thermal management systems frequently operate well within the 50-500W range, occupying the middle to upper end of this spectrum.

### Low-to-Medium Power Applications: Actuators and Comfort Systems

While thermal management demands high power, a multitude of other auxiliary functions are performed by DC motors with significantly lower power ratings. These applications often involve intermittent actuation for comfort and convenience features. Analysis of components from major suppliers like Bosch and Nidec reveals that these motors typically operate well below the 50W threshold.

A prime example is the Bosch FPG 2, a 12V DC motor commonly used for automotive window regulators. Technical datasheets for this model specify a nominal power of just 14W. This motor, which weighs approximately 0.59 kg, is designed for the short, high-torque bursts required to raise and lower a window. Its power consumption is representative of many similar actuation tasks within a vehicle. Bosch documentation further notes that its portfolio of DC motors, used for applications from seat adjustment to wiping systems, operates in a 12V to 24V range, emphasizing robust design and a favorable power-to-weight ratio rather than high continuous power output.

Further evidence of low-power DC motor use is found in windshield wiper systems. A datasheet for a specific Nidec automotive wiper motor, the Series GMPD Motor type 405 061, lists a nominal power output of only 3.95W. This brushed DC motor is designed to provide the necessary torque for wiper arm movement at a very low power draw. The datasheet for this particular component lists a weight of "0.000 kg," which is evidently a placeholder or an indication that the motor's mass is considered negligible in the context of its primary specifications, rather than a literal measurement. This anomaly highlights the challenge of obtaining complete and consistent data but does not detract from the key finding regarding its low power rating.

Information regarding power seat motors, such as those supplied by Brose, also points toward a more complex, controlled approach rather than high power. While specific power and weight figures for their 2024-2026 BEV seat motors are not publicly detailed, Brose describes its next-generation systems as using brushless DC motors with integrated electronics. These systems are designed for high efficiency, variable adjustment speeds, and direct integration into the vehicle's electronics architecture via CAN or LIN bus control. A single power seat can have up to 10 motors for 20-way adjustment, suggesting that each individual motor is a small, precisely controlled unit rather than a single high-power motor. The focus is on distributed intelligence and efficiency, which aligns with the characteristics of low-power DC motor applications.

## Analysis of Stepper Motors in BEV Auxiliary Systems

Stepper motors are a distinct class of electric motor renowned for their ability to rotate in precise, discrete steps. This characteristic makes them ideal for applications requiring accurate positioning and control without the need for complex feedback sensors like encoders. In modern BEVs, stepper motors are ubiquitously employed in a variety of auxiliary mechatronic systems where precision is more critical than speed or power. The available data consistently shows that these motors are low-power devices, with consumption figures that fall substantially below the 50W mark.

### Precision Control in Lighting and Aerodynamic Systems

One of the key safety and technology features in modern vehicles is the adaptive front-lighting system (AFS), which dynamically adjusts the headlight beams to improve visibility and reduce glare for oncoming drivers. These systems rely on stepper motors for their precise and repeatable movements. A typical headlight leveling motor is a compact and lightweight component, weighing approximately 90 grams (0.2 lbs). While direct power ratings are seldom published, power consumption can be estimated based on electrical characteristics. For example, a stepper motor driven with a maximum current of 1.5A on a 12V or 24V system would have a theoretical maximum power dissipation of 18W or 36W, respectively. However, industry sources note that the actual power drawn is often significantly lower, as the motor only consumes peak current during movement and consumes very little power while holding its position. This places headlight leveling motors firmly in the low-power category.

Another innovative application for stepper motors is in active grille shutter (AGS) systems. These systems improve vehicle aerodynamics and thermal efficiency by opening or closing shutters in the front grille to control airflow. The actuation is managed by a stepper motor, typically operating on the vehicle's 12V supply and controlled via a LIN bus connection to the main vehicle computer. While specific datasheets for the exact stepper motors used in AGS for 2024-2026 models are not publicly available, their operational profile—requiring precise, intermittent adjustments rather than continuous high-torque output—is consistent with low-power stepper motor technology. General-purpose stepper motors with similar size and torque characteristics, such as the NEMA 17, are often used as reference points and feature low power consumption.

### Climate Control and Other Low-Power Actuations

Within the vehicle cabin, stepper motors are essential for the operation of the HVAC system's blend doors. These actuators control small flaps that mix hot and cold air to achieve the precise temperature selected by the occupants. The use of stepper motors provides the necessary positional accuracy for consistent and reliable temperature regulation. Manufacturers of these components emphasize their low electrical power consumption and energy efficiency. Although specific wattages are not provided in general datasheets, the nature of the task—moving a small, low-friction door within a plastic housing—implies a minimal power requirement, likely in the single-digit watt range.

A notable finding from the research concerns actuators for EV-specific functions, such as the charging port door. While the initial query explored the use of stepper motors for this application, the data reveals a trend towards using smart, programmable Brushless DC (BLDC) motor actuators instead. These integrated mechatronic units, supplied by companies like NMB Technologies and Magna, often include LIN bus communication, position sensing, and safety features like anti-pinch and ice-breaking functions. This indicates that for certain new BEV applications requiring more complex logic and higher torque in a compact package, intelligent BLDC drives are being favored over traditional stepper motors. This finding itself underscores the ongoing technological refinement in BEV auxiliary systems.

## Conclusion: Assessment of the 50-500W Power Range

The research objective of this report was to document the power and weight specifications of medium DC and stepper motors in modern BEV auxiliary systems and to determine the accuracy of the 50-500W power range as a classification for these components. Based on a detailed analysis of data from leading automotive suppliers, it is clear that this range is only partially accurate and fails to represent the full diversity of auxiliary motor applications.

The 50-500W range is valid for a critical but limited segment of high-load, thermally-essential auxiliary systems. Brushless DC motors used for HVAC blowers (up to 300W) and electric coolant pumps for battery and powertrain thermal management (with market segments extending to 400W and beyond) fit squarely within this classification. These applications are characterized by their need for sustained power output and are engineered for high efficiency to mitigate their significant impact on the BEV's overall energy budget.

However, the 50-500W range entirely excludes two major categories of auxiliary motors. The first is the vast number of low-power DC motors used for intermittent actuation in comfort and convenience systems. As demonstrated by window regulator motors (14W) and wiper motors (~4W), these ubiquitous components operate at power levels an order of magnitude below the 50W threshold. The second excluded category is stepper motors. Across all investigated applications—including headlight leveling, active grille shutters, and HVAC blend doors—stepper motors are fundamentally low-power devices, with estimated maximum consumption typically below 40W and often operating in the single-digit watt range. Their value lies in precision control, not power output.

Therefore, a single 50-500W definition for "medium motors" is misleading. A more accurate framework would involve segmenting auxiliary motors by both application and technology:

1.  **High-Power Auxiliary Motors (50W - 500W+):** Primarily brushless DC motors used for continuous or high-demand thermal management (HVAC blowers, liquid coolant pumps).
2.  **Low-Power Auxiliary Motors (< 50W):** A broad category that includes:
    *   **Brushed/Brushless DC Actuators (3W - 25W):** Used for intermittent, torque-based tasks like window lifts, seat adjustments, and wipers.
    *   **Stepper Motor Actuators (< 40W):** Used for high-precision positioning tasks such as headlight leveling, blend door control, and grille shutter actuation.

The trend in 2024-2026 BEVs is toward greater intelligence and efficiency across all motor types. The increasing prevalence of brushless DC motors and the integration of LIN/CAN bus control even for low-power actuators underscore the industry's focus on minimizing every watt of energy consumption. In conclusion, while the term "medium motor" may be a convenient shorthand, it lacks the technical specificity required for accurate engineering and market analysis in the sophisticated electrical landscape of modern battery electric vehicles.

# References
1. [Professional solutions for your projects. - Bosch iBusiness](https://www.bosch-ibusiness.com/media/images/products/dc_motors/xx_pdfs_2/pac_i-buisness_e-motors_21_22_cat_en_cd2016_82263.pdf)
2. [Bosch Motor DC 12V data sheet pdf - Scribd](https://www.scribd.com/document/371672982/Bosch-Motor-DC-12V-data-sheet-pdf)
3. [Bosch Motor DC 12V Data sheet - Scribd](https://www.scribd.com/document/338584632/Bosch-Motor-DC-12V-Data-sheet)
4. [Bosch Motor DC 12V Data Sheet PDF - PDF Coffee](https://pdfcoffee.com/bosch-motor-dc-12v-data-sheet-pdf-free.html)
5. [Bosch window lifter motor catalog.pdf - Scribd](https://www.scribd.com/document/406578868/Bosch-window-lifter-motor-catalog-pdf)
6. [Motori elettrici - Bosch Aftermarket](https://www.boschaftermarket.com/xrm/media/images/country_specific/it/xx_pdfs_28/parts_5/motori_elettrici.pdf)
7. [Other - 2024 Brose motor for Specialized? | EMTB Forums - EMTB Forums](https://www.emtbforums.com/threads/2024-brose-motor-for-specialized.34697/)
8. [New Brose Drive 3 is the next ebike drive with a 48-volt system - eBike24.com](https://www.ebike24.com/blog/ebike-brose-drive-3)
9. [Caution: High voltage! – Brose present the eagerly awaited Drive³ Peak motor in the 48V system and a concept motor with an integrated stepless drivetrain | E-MOUNTAINBIKE Magazine - E-MOUNTAINBIKE Magazine](https://ebike-mtb.com/en/brose-drive-3-peak-motor-48v-system-and-concept-drive/)
10. [eSystems – Brose for 2024 – eBikes Int'l - eBikes Int'l](https://ebikes-international.com/esystems-brose-for-2024/)
11. [Brose Drive³ Peak marks shift to 48V e-bike motors for 2024 and beyond | electric bike reviews, buying advice and news - ebiketips - ebiketips](https://ebiketips.road.cc/content/news/brose-drive-peak-marks-shift-to-48v-e-bike-motors-for-2024-and-beyond-4629)
12. [Brose Fahrzeugteile SE & Co. KG, Coburg - MarkLines Automotive Industry Portal - MarkLines](https://www.marklines.com/en/top500/brose-fahrzeugteile)
13. [Brose Presents New Drive3 with 48-volt System, Concept Drive, Reman Drive and More for 2024 – eBikes Int'l - eBikes Int'l](https://ebikes-international.com/brose-presents-new-drive3-with-48-volt-system-concept-drive-reman-drive-and-more-for-2024/)
14. [German Firm Brose Introduces Powerful New 48-Volt E-Bike System - InsideEVs](https://insideevs.com/news/673216/brose-drive-3-peak-ebike-motor/)
15. [Adjustment systems for front and rear seats - Brose](https://www.brose.com/de-en/products/adjustment-systems-for-front-and-rear-seats/)
16. [Valeo Dual Wheel Blower Assembly for BH1600 Units, 12V - Amazon](https://www.amazon.com/Valeo-Wheel-Blower-Assembly-BH1600/dp/B0C7CZFJZ6)
17. [Valeo Dual Wheel Blower Assembly with Resistor, 12V - Amazon](https://m.media-amazon.com/images/I/516kHHw3IYL.jpg)
18. [VW HVAC Blower Motor - Valeo 1K1819015F - FCP Euro](https://www.rmeuropean.com/Images/BigPictures/1K1819015F-MFG262-2.jpg)
19. [HVAC Brushless Motors - Valeo](https://www.valeo.com/en/catalogue/ths/hvac-brushless-motors/)
20. [Valeo HVAC Blower Motor - FindItParts](https://www.finditparts.com/t/16250/manufacturer/valeo/categories/hvac/motors-core-case-and-related-components/hvac-blower-motor/)
21. [Valeo™ | HVAC Blower Motors — CARiD.com - CARiD.com](https://www.carid.com/valeo/hvac-blower-motor.html)
22. [Valeo 698262 HVAC Blower Motor - PartsHawk](https://partshawk.com/valeo-698262-hvac-blower-motor.html)
23. [Blower parts from VALEO for your car — buy online - TRODO](https://www.trodo.com/blower-parts/valeo)
24. [Valeo Blower Motor - Europa Parts](https://www.europaparts.com/brands/valeo/blower-motor.html)
25. [Press Releases - Continental](https://www.continental.com/en/press/press-releases/water-pump/)
26. [Water Pumps - Continental Engine Parts](https://www.continental-engineparts.com/sa/en-us/automotive-aftermarket/products/components/water-pumps)
27. [New auxiliary water pumps for hybrid and electric vehicles - Continental Aftermarket](https://www.continental-aftermarket.com/en-en/magazine/technology-products/new-auxiliary-water-pumps-for-hybrid-and-electric-vehicles)
28. [Global Electric Coolant Pump for Passenger Cars Market 2021 to 2025 - Key Players Include Aisin Seiki, Buhler Motor, Continental, Among Others - GlobeNewswire](https://www.globenewswire.com/news-release/2021/03/02/2185046/28124/en/Global-Electric-Coolant-Pump-for-Passenger-Cars-Market-2021-to-2025-Key-Players-Include-Aisin-Seiki-Buhler-Motor-Continental-Among-Others.html)
29. [Continental Hybrid Coolant Pumps - Continental Aftermarket](https://www.continental-aftermarket.com/media/5388/continental-hybrid-coolant-pumps.pdf)
30. [Water pumps for ancillary drives - Continental Engine Parts](https://www.continental-engineparts.com/eu/en-gb/aftermarket/products/components/water-pumps-for-ancillary-drives)
31. [Press Releases - Continental](https://www.continental.com/en/press/press-releases/new-products-for-thermal-management/)
32. [OEMDP_Water-Pump_Conti_2021.pdf - Continental Aftermarket](https://www.continental-aftermarket.com/media/3211/oemdp_water-pump_conti_2021.pdf)
33. [Electric Centrifugal Pump for Coolant Market Research Report - Archive Market Research](https://www.archivemarketresearch.com/reports/electric-centrifugal-pump-for-coolant-110020)
34. [New Continental Hybrid Inverter Coolant Pumps Expand Aftermarket Offering for OE Hybrid Parts - Continental Aftermarket](https://www.continental-aftermarket.com/us-en/press/press-releases/2020/2020-11-30-new-continental-hybrid-inverter-coolant-pumps-expand-aftermarket-offering-for-oe-hybrid-parts/)
35. [Motor Datasheet (PDF) - Nidec Motors & Actuators - Yumpu](https://www.yumpu.com/en/document/view/35123021/motor-datasheet-pdf-nidec-motors-actuators)
36. [Product Data Sheets - Nidec ACIM](https://acim.nidec.com/en/motors/usmotors/Products-And-Services/Catalogs-And-Literature/Literature/Product-Data-Sheets)
37. [Download - Nidec](https://www.nidec.com/en/nidec-technomotor/product/download/)
38. [Technical Data - Nidec ACIM](https://acim.nidec.com/en/motors/usmotors/Service-And-Support/Technical-Data)
39. [wiper motor 12v dc specifications Datasheet, PDF - Datasheet Archive](https://www.datasheetarchive.com/wiper%20motor%2012v%20dc%20specifications-datasheet.html)
40. [Nidec - Datasheets by GlobalSpec - GlobalSpec](https://datasheets.globalspec.com/ds/17/Nidec)
41. [Nidec Corporation - MarkLines Automotive Industry Portal - MarkLines](https://www.marklines.com/en/top500/nidec)
42. [Data Sheets - Nidec ACIM](https://acim.nidec.com/en/drives/control-techniques/Downloads/Data-Sheets)
43. [Active Grille Shutter Wiring - Looking to Modify - CruzeTalk](https://www.cruzetalk.com/threads/active-grille-shutter-wiring-looking-to-modify.256492/)
44. [Dorman 601-315 Active Grille Shutter - Dorman Products](https://www.dormanproducts.com/p-98659-601-315.aspx)
45. [NAPA OE Solutions Radiator Shutter Assembly - NAPA Auto Parts](https://www.napaonline.com/en/p/NOE601341)
46. [Dorman 601-326 Active Grille Shutter - Dorman Products](https://www.dormanproducts.com/p-130476-601-326.aspx)
47. [L3Z-10884-A Active Grille Shutter Compatible with Expedition & Navigator 2018-2024 - Amazon](https://i.ebayimg.com/images/g/kn4AAOSwcl1kZERT/s-l1200.jpg)
48. [Active Grill Shutters not working even after replacing motor - 5th Gen RAMs Forum](https://5thgenrams.com/community/threads/active-grill-shutters-not-working-even-after-replacing-motor.58856/)
49. [Radiator Shutter Assembly with Motor Actuator Compatible with 2013-2018 & 2019-2021 - Amazon](https://www.amazon.com/Radiator-Actuator-Compatible-2013-2018-2019-2021/dp/B09MMM9FF5)
50. [NEMA17 Stepper Motor Datasheet PDF, 1.5 A, 1.8° Stepper Motor and Dimensions - UTSource](https://www.utmel.com/components/nema17-stepper-motor-datasheet-pdf-1-5-a-1-8%C2%B0-stepper-motor-and-dimensions?id=914)
51. [28BYJ-48 12V Stepper Motor Datasheet - Aksotronik](https://www.aksotronik.com.pl/media/products_files/009433.pdf)
52. [Roneeson Active Grille Shutter for 2017-2019 & 2017-2018 - Amazon](https://i.ebayimg.com/images/g/L8sAAOSwsRxk8X6N/s-l1200.jpg)
53. [Headlight adjustment stepper motor calibration - BimmerFest](https://www.bimmerfest.com/threads/headlight-adjustment-stepper-motor-calibration.588252/)
54. [Stepper motor and power consumption - Reddit](https://www.reddit.com/r/hobbycnc/comments/tiguj5/stepper_motor_and_power_consumption/)
55. [Headlight Leveling Motor - Connector Experts](https://connectorexperts.com/i-24976516-headlight-leveling-motor.html)
56. [Automotive Headlight Swivel and Leveling With Stepper Motors Reference Design - Texas Instruments](https://www.ti.com/tool/TIDA-020026)
57. [Headlamp levelling system - HELLA Tech World](https://www.hella.com/techworld/us/technical/automotive-lighting/headlamp-levelling-system/)
58. [Understanding how much power a stepper motor draws - Electrical Engineering Stack Exchange](https://electronics.stackexchange.com/questions/313880/understanding-how-much-power-a-stepper-motor-draws)
59. [Stepper motors assist adaptive headlights - EE Times](https://www.eetimes.com/stepper-motors-assist-adaptive-headlights/)
60. [DRV8889-Q1 Automotive Stepper Motor Driver With Integrated Current Sense and Stall Detection - Texas Instruments](https://www.ti.com/lit/ta/sszt370/sszt370.pdf?ts=1770265532661)
61. [Stepper Motor Calculator - Do Supply](https://www.dosupply.com/tech/2022/02/07/stepper-motor-calculator/)
62. [Mercedes-Benz HVAC Blend Door Actuator - MB Parts](https://mbparts.mbusa.com/oem-parts/mercedes-benz-hvac-blend-door-actuator-9069208)
63. [Saab Blend Door Actuator (Stepper Motor) - eSaabParts](https://www.esaabparts.com/saab/parts/13192013)
64. [HVAC Heater Blend Door Actuator - Duallane Truck Parts](https://www.duallane.com/shop-parts/hvac/hvac-blowers-controls/hvac-heater-blend-door-actuator)
65. [Ford HVAC Blend Door Actuator Motor - Ford Parts](https://parts.ford.com/shop/en/us/ac-repair-parts/hvac-blend-door-actuator-motor-p-yh1779)
66. [HVAC Blend Door Actuator - Ford](https://www.ford.com/product/hvac-blend-door-actuator-p4000095841)
67. [ACDelco 15-74122 GM Original Equipment HVAC Stepper Motor - Amazon](https://www.amazon.com/ACDelco-15-74122-Original-Equipment-Actuator/dp/B005OXVO5S)
68. [Highlander HVAC Heater A/C Blend Air Door Actuator Control Motor - Amazon](https://i.ytimg.com/vi/60fpt9-12-0/maxresdefault.jpg)
69. [Stepper Motor Actuator for HVAC Blend Door A Review - Academia.edu](https://www.academia.edu/86608156/Stepper_Motor_Actuator_for_HVAC_Blend_Door_A_Review)
70. [STEPPER MOTOR ACTUATOR FOR HVAC BLEND DOOR A REVIEW - Academia.edu](https://www.academia.edu/40175828/STEPPER_MOTOR_ACTUATOR_FOR_HVAC_BLEND_DOOR_A_REVIEW)
71. [AMP+ Charging Inlet Actuators - TE Connectivity](https://www.te.com/en/products/connectors/automotive-connectors/intersection/amp-charging-inlet-actuators.html)
72. [Charge Port Door System - NMB Technologies Corporation](https://nmbtc.com/product-category/charge-port-door-system/)
73. [Mini Drive Motor Battery Pack Charging Port Door Release Actuator - Mini Parts Direct](https://www.minipartsdirect.com/oem-parts/mini-drive-motor-battery-pack-charging-port-door-release-actuator-61139343121)
74. [Module - Ford](https://www.ford.com/product/module-p4000025226)
75. [SmartAccess™ Charge Port Door - Magna](https://www.magna.com/products/exterior-interior/mechatronics/smartaccess-chargeportdoor)
76. [Charge Port Door Actuator - Motion Controls International](https://www.motioncontrols.com/cases/charge-port-door-actuator)
77. [AMP+ Charging Inlets Brochure - TE Connectivity](https://www.te.com/content/dam/te-com/documents/automotive/global/amp-plus-charging-inlets-brochure.pdf)
78. [Land Rover Drive Motor Battery Pack Charging Port Door Release Actuator - Land Rover Cary](https://parts.landrovercary.com/oem-parts/land-rover-drive-motor-battery-pack-charging-port-door-release-actuator-lr169952)