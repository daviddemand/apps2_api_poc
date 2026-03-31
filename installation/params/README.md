## Module Parameters
Module-level param provides functionality to set user-defined, custom parameters in the Module Wizard and use them across the Module.

| Property  | Description |
| ------------- | ------------- |
| name  | Parameter name that should be in CamelCase  |
| typeId  | 0, 1, 3, 8, 90, 150, 160, 170 (Text, Number, Yes/No, Password, SQL Query Selector, User Selector, Latitude, Longitude)  |
| value  | Empty or pre-defined value  |
| paramSql  | SQL statement to interact with the user's environment  |
| description  | Description for the parameter |
| isReadOnly  | Control modifying access after installation/upgrade through GUI  |
| isHidden  | If true parameter will not be displayed and will be skipped  |

They can be accessible while installation/upgrade/uninstallation or after them through: 
- GUI in the Module Parameters tab
- `util_module` functions
- `{ParamName}` placeholder inside of .MD, .XML, .SQL, .CSV files being replaced with the parameter actual value.

```sql
--- SQL Usage
util.newtrackor(id.{ParamName}.tt)
--or
util_module.get_module_param_val(:p_module_id, 'ParamName')
```

``````xml
<!--XML Usage-->
<TRACKOR_TYPE>{ParamName}</TRACKOR_TYPE> 
``````

CSV Usage

| {ParamName} ID |
| --- |
| VHM-{ParamName} |
