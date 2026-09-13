# Club configuration index

No independently verified current club calibration profile has been established
in this repository. Do not initialize one by copying the personal TX2 values.

| Existing material | Scope |
| --- | --- |
| [Ansible inventory](../../../ansible/production), target `robot` | Club deployment selection |
| [Legacy ROS model](../../../model/README.md) and [URDF](../../../model/robomo.urdf) | Older visualization/TF workflow; geometry is not a verified club calibration |
| [Sabertooth settings](../../../sabertooth_settings/README.md) | Existing controller configuration files; confirm hardware and variant before applying |
| [Historical ROS configurations](../../../notebooks/README.md) | Legacy notebook/ROS workflow; not a current measured club profile |

Store newly verified club-specific configuration here and update its consumers
as part of deployment work. The root `config/tx2*`, `base-calibration.json` and
`realsense-obstacles.yaml` files are indexed under the personal robot.
