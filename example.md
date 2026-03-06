#SysReq-Ref
| #                                           | Input                        | Output                               | Design Spec Reference                |
| ------------------------------------------- | ---------------------------- | ------------------------------------ | ------------------------------------ |
| HMI_TC_MAX_RPM                              | HMI_TC_RED_START_RPM (a)     | Scale Number to use                  |
| 1                                           | 60[6000rpm]                  | 39[3900rpm]<=(a) <=40[4000rpm]       | 6000RPM_Scale_Number[0]-[3] : 【\*1】  | Refer to Godot Design |
| 6000RPM_Scale_Number[4]-[6] : Red display   |
| 2                                           | 40[4000rpm]<(a)<=50[5000rpm] | 6000RPM_Scale_Number[0]-[4] : 【\*1】  |
| 6000RPM_Scale_Number[5]-[6] : Red display   |
| 3                                           | 70[7000rpm]                  | 39[3900rpm]<=(a) <=40[4000rpm]       | 7000RPM_Scale_Number[0]-[3] : 【\*1】  |
| 7000RPM_Scale_Number[4]-[7] : Red display   |
| 4                                           | 40[4000rpm]<(a)<=50[5000rpm] | 7000RPM_Scale_Number[0]-[4] : 【\*1】  |
| 7000RPM_Scale_Number[5]-[7] : Red display   |
| 5                                           | 50[5000rpm]<(a)<=60[6000rpm] | 7000RPM_Scale_Number[0]-[5] : 【\*1】  |
| 7000RPM_Scale_Number[6]-[7] : Red display   |
| 6                                           | 80[8000rpm]                  | 39[3900rpm]<=(a) <=40[4000rpm]       | 8000RPM_Scale_Number[0]-[3] : 【\*1】  |
| 8000RPM_Scale_Number[4]-[8] : Red display   |
| 7                                           | 40[4000rpm]<(a)<=50[5000rpm] | 8000RPM_Scale_Number[0]-[4] : 【\*1】  |
| 8000RPM_Scale_Number[5]-[8] : Red display   |
| 8                                           | 50[5000rpm]<(a)<=60[6000rpm] | 8000RPM_Scale_Number[0]-[5] : 【\*1】  |
| 8000RPM_Scale_Number[6]-[8] : Red display   |
| 9                                           | 60[6000rpm]<(a)<=70[7000rpm] | 8000RPM_Scale_Number[0]-[6] : 【\*1】  |
| 8000RPM_Scale_Number[7]-[8] : Red display   |
| 10                                          | 90[9000rpm]                  | 39[3900rpm]<=(a) <=40[4000rpm]       | 9000RPM_Scale_Number[0]-[3] : 【\*1】  |
| 9000RPM_Scale_Number[4]-[9] : Red display   |
| 11                                          | 40[4000rpm]<(a)<=50[5000rpm] | 9000RPM_Scale_Number[0]-[4] : 【\*1】  |
| 9000RPM_Scale_Number[5]-[9] : Red display   |
| 12                                          | 50[5000rpm]<(a)<=60[6000rpm] | 9000RPM_Scale_Number[0]-[5] : 【\*1】  |
| 9000RPM_Scale_Number[6]-[9] : Red display   |
| 13                                          | 60[6000rpm]<(a)<=70[7000rpm] | 9000RPM_Scale_Number[0]-[6] : 【\*1】  |
| 9000RPM_Scale_Number[7]-[9] : Red display   |
| 14                                          | 70[7000rpm]<(a)<=80[8000rpm] | 9000RPM_Scale_Number[0]-[7] : 【\*1】  |
| 9000RPM_Scale_Number[8]-[9] : Red display   |
| 15                                          | 100[10000rpm]                | 39[3900rpm]<=(a) <=40[4000rpm]       | 10000RPM_Scale_Number[0]-[3] : 【\*1】 |
| 10000RPM_Scale_Number[4]-[10] : Red display |
| 16                                          | 40[4000rpm]<(a)<=50[5000rpm] | 10000RPM_Scale_Number[0]-[4] : 【\*1】 |
| 10000RPM_Scale_Number[5]-[10] : Red display |
| 17                                          | 50[5000rpm]<(a)<=60[6000rpm] | 10000RPM_Scale_Number[0]-[5] : 【\*1】 |
| 10000RPM_Scale_Number[6]-[10] : Red display |
| 18                                          | 60[6000rpm]<(a)<=70[7000rpm] | 10000RPM_Scale_Number[0]-[6] : 【\*1】 |
| 10000RPM_Scale_Number[7]-[10] : Red display |
| 19                                          | 70[7000rpm]<(a)<=80[8000rpm] | 10000RPM_Scale_Number[0]-[7] : 【\*1】 |
| 10000RPM_Scale_Number[8]-[10] : Red display |
| 20                                          | 80[8000rpm]<(a)<=90[9000rpm] | 10000RPM_Scale_Number[0]-[8] : 【\*1】 |
| 10000RPM_Scale_Number[9]-[10] : Red display |
| 21                                          | Other than above             | No Display(Not applicable)           | NA                                   |

#SysReq-Actual

| #  | Input            | Input                          | Output                                      | Design Spec Reference |
| -- | ---------------- | ------------------------------ | ------------------------------------------- | --------------------- |
|    | HMI_TC_MAX_RPM   | HMI_TC_RED_START_RPM (a)       | Scale Number to use                         |                       |
| 1  | 60[6000rpm]      | 39[3900rpm]<=(a) <=40[4000rpm] | 6000RPM_Scale_Number[0]-[3] : 【\*1】         | Refer to Godot Design |
| 2  | 60[6000rpm]      | 39[3900rpm]<=(a) <=40[4000rpm] | 6000RPM_Scale_Number[4]-[6] : Red display   |                       |
| 3  | 60[6000rpm]      | 40[4000rpm]<(a)<=50[5000rpm]   | 6000RPM_Scale_Number[0]-[4] : 【\*1】         |                       |
| 4  | 60[6000rpm]      | 40[4000rpm]<(a)<=50[5000rpm]   | 6000RPM_Scale_Number[5]-[6] : Red display   |                       |
| 5  | 70[7000rpm]      | 39[3900rpm]<=(a) <=40[4000rpm] | 7000RPM_Scale_Number[0]-[3] : 【\*1】         |                       |
| 6  | 70[7000rpm]      | 39[3900rpm]<=(a) <=40[4000rpm] | 7000RPM_Scale_Number[4]-[7] : Red display   |                       |
| 7  | 70[7000rpm]      | 40[4000rpm]<(a)<=50[5000rpm]   | 7000RPM_Scale_Number[0]-[4] : 【\*1】         |                       |
| 8  | 70[7000rpm]      | 40[4000rpm]<(a)<=50[5000rpm]   | 7000RPM_Scale_Number[5]-[7] : Red display   |                       |
| 9  | 70[7000rpm]      | 50[5000rpm]<(a)<=60[6000rpm]   | 7000RPM_Scale_Number[0]-[5] : 【\*1】         |                       |
| 10 | 70[7000rpm]      | 50[5000rpm]<(a)<=60[6000rpm]   | 7000RPM_Scale_Number[6]-[7] : Red display   |                       |
| 11 | 80[8000rpm]      | 39[3900rpm]<=(a) <=40[4000rpm] | 8000RPM_Scale_Number[0]-[3] : 【\*1】         |                       |
| 12 | 80[8000rpm]      | 39[3900rpm]<=(a) <=40[4000rpm] | 8000RPM_Scale_Number[4]-[8] : Red display   |                       |
| 13 | 80[8000rpm]      | 40[4000rpm]<(a)<=50[5000rpm]   | 8000RPM_Scale_Number[0]-[4] : 【\*1】         |                       |
| 14 | 80[8000rpm]      | 40[4000rpm]<(a)<=50[5000rpm]   | 8000RPM_Scale_Number[5]-[8] : Red display   |                       |
| 15 | 80[8000rpm]      | 50[5000rpm]<(a)<=60[6000rpm]   | 8000RPM_Scale_Number[0]-[5] : 【\*1】         |                       |
| 16 | 80[8000rpm]      | 50[5000rpm]<(a)<=60[6000rpm]   | 8000RPM_Scale_Number[6]-[8] : Red display   |                       |
| 17 | 80[8000rpm]      | 60[6000rpm]<(a)<=70[7000rpm]   | 8000RPM_Scale_Number[0]-[6] : 【\*1】         |                       |
| 18 | 80[8000rpm]      | 60[6000rpm]<(a)<=70[7000rpm]   | 8000RPM_Scale_Number[7]-[8] : Red display   |                       |
| 19 | 90[9000rpm]      | 39[3900rpm]<=(a) <=40[4000rpm] | 9000RPM_Scale_Number[0]-[3] : 【\*1】         |                       |
| 20 | 90[9000rpm]      | 39[3900rpm]<=(a) <=40[4000rpm] | 9000RPM_Scale_Number[4]-[9] : Red display   |                       |
| 21 | 90[9000rpm]      | 40[4000rpm]<(a)<=50[5000rpm]   | 9000RPM_Scale_Number[0]-[4] : 【\*1】         |                       |
| 22 | 90[9000rpm]      | 40[4000rpm]<(a)<=50[5000rpm]   | 9000RPM_Scale_Number[5]-[9] : Red display   |                       |
| 23 | 90[9000rpm]      | 50[5000rpm]<(a)<=60[6000rpm]   | 9000RPM_Scale_Number[0]-[5] : 【\*1】         |                       |
| 24 | 90[9000rpm]      | 50[5000rpm]<(a)<=60[6000rpm]   | 9000RPM_Scale_Number[6]-[9] : Red display   |                       |
| 25 | 90[9000rpm]      | 60[6000rpm]<(a)<=70[7000rpm]   | 9000RPM_Scale_Number[0]-[6] : 【\*1】         |                       |
| 26 | 90[9000rpm]      | 60[6000rpm]<(a)<=70[7000rpm]   | 9000RPM_Scale_Number[7]-[9] : Red display   |                       |
| 27 | 90[9000rpm]      | 70[7000rpm]<(a)<=80[8000rpm]   | 9000RPM_Scale_Number[0]-[7] : 【\*1】         |                       |
| 28 | 90[9000rpm]      | 70[7000rpm]<(a)<=80[8000rpm]   | 9000RPM_Scale_Number[8]-[9] : Red display   |                       |
| 29 | 100[10000rpm]    | 39[3900rpm]<=(a) <=40[4000rpm] | 10000RPM_Scale_Number[0]-[3] : 【\*1】        |                       |
| 30 | 100[10000rpm]    | 39[3900rpm]<=(a) <=40[4000rpm] | 10000RPM_Scale_Number[4]-[10] : Red display |                       |
| 31 | 100[10000rpm]    | 40[4000rpm]<(a)<=50[5000rpm]   | 10000RPM_Scale_Number[0]-[4] : 【\*1】        |                       |
| 32 | 100[10000rpm]    | 40[4000rpm]<(a)<=50[5000rpm]   | 10000RPM_Scale_Number[5]-[10] : Red display |                       |
| 33 | 100[10000rpm]    | 50[5000rpm]<(a)<=60[6000rpm]   | 10000RPM_Scale_Number[0]-[5] : 【\*1】        |                       |
| 34 | 100[10000rpm]    | 50[5000rpm]<(a)<=60[6000rpm]   | 10000RPM_Scale_Number[6]-[10] : Red display |                       |
| 35 | 100[10000rpm]    | 60[6000rpm]<(a)<=70[7000rpm]   | 10000RPM_Scale_Number[0]-[6] : 【\*1】        |                       |
| 36 | 100[10000rpm]    | 60[6000rpm]<(a)<=70[7000rpm]   | 10000RPM_Scale_Number[7]-[10] : Red display |                       |
| 37 | 100[10000rpm]    | 70[7000rpm]<(a)<=80[8000rpm]   | 10000RPM_Scale_Number[0]-[7] : 【\*1】        |                       |
| 38 | 100[10000rpm]    | 70[7000rpm]<(a)<=80[8000rpm]   | 10000RPM_Scale_Number[8]-[10] : Red display |                       |
| 39 | 100[10000rpm]    | 80[8000rpm]<(a)<=90[9000rpm]   | 10000RPM_Scale_Number[0]-[8] : 【\*1】        |                       |
| 40 | 100[10000rpm]    | 80[8000rpm]<(a)<=90[9000rpm]   | 10000RPM_Scale_Number[9]-[10] : Red display |                       |
| 41 | Other than above |                                | No Display(Not applicable)                  | NA                    |

#TC-Actual

| Issue ID                 | Summary                                                | Test Type | Issue Type | Project Key | Assignee | Description            | Action                         | Data                                                                                                                                       | Expected Result                                                        | Planned Execution | Test Case Type     | Feature Group                                        | Components | Labels           | LinkTest          |
| ------------------------ | ------------------------------------------------------ | --------- | ---------- | ----------- | -------- | ---------------------- | ------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------- | ----------------- | ------------------ | ---------------------------------------------------- | ---------- | ---------------- | ----------------- |
| TFDCX32348-137314_TC_001 | [Scale Number to use for HMI_TC_MAX_RPM = 40[4000rpm]] | PROVEtech | Test       | TCTOIC      | ENGG     | Confidence Score: 0.95 | 1\. Voltage= 12V<br>2\. Bat-ON | 1) Set HMI_TC_MAX_RPM = 40[4000rpm]<br><br>2) Trigger action...<br><br>3) Verify Scale Number to use is 6000RPM_Scale_Number[0]-[4]: 【\*1】 | Verify Scale Number to use is 6000RPM_Scale_Number[5]-[6]: Red display | Manual            | Feature Functional | Scale Number to use for HMI_TC_MAX_RPM = 40[4000rpm] | SW_DI_FV   | AI Generated TCs | TFDCX32348-137314 |
| TFDCX32348-137314_TC_002 | [Invalid input for HMI_TC_MAX_RPM]                     | PROVEtech | Test       | TCTOIC      | ENGG     | Confidence Score: 0.95 | 1\. Voltage= 12V<br>2\. Bat-ON | 1) Set HMI_TC_MAX_RPM = -10<br><br>2) Trigger action...<br><br>3) Verify error handling: Invalid input value                               | Verify error handling: Invalid input value                             | Manual            | Feature Functional | Invalid input for HMI_TC_MAX_RPM                     | SW_DI_FV   | AI Generated TCs | TFDCX32348-137314 |