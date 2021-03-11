
from eieio.meter.xrite.i1pro import I1Pro
from eieio.meter.meter_abstractions import Mode  # , IntegrationType, Observer


def exercise_connected_i1pro(calibrate_only=False, wait_for_button_press=True):
    meter = None
    try:
        meter = I1Pro()
        print(f"{meter.model()} s/n {meter.serial_number()}")
        print(f"using {meter.make()} SDK {meter.sdk_version()}")
        print(f"via EIEIO adapter {meter.adapter_version()}, Python driver {meter.adapter_module_version()}")
        # test ability to calibrate all modes
        for mode in [Mode.EMISSIVE, Mode.reflective, Mode.AMBIENT]:
            try:
                print(f"attempting to set and calibrate {mode.name} mode...", end='')
                meter.set_measurement_mode(Mode.EMISSIVE)
                print("EMISSIVE mode set...", end='')
            except IOError as e:
                print(f"failed I/O (setting measurement mode to {mode.name}): {e}")
                return
            try:
                print("calibrating...", end='')
                meter.calibrate(wait_for_button_press)
                print("calibrated")
            except IOError as e:
                print(f"failed I/O (calibrating for mode {mode.name}): {e}")
            if not calibrate_only:
                prompt = "patch name ('exit' to exit): "
                with open("/var/tmp/mes.txt", "a") as file:
                    while True:
                        patch = input(prompt)
                        if patch == 'exit':
                            break
                        try:
                            print("attempting to trigger i1Pro...", end='')
                            meter.trigger_measurement()
                            print("triggered")
                        except IOError as e:
                            print(f"failed I/O (triggering measurement): {e}")
                            return
                        try:
                            cap_x, cap_y, cap_z = meter.colorimetry()
                            entry = f"{patch}: X {cap_x:.4f}, Y {cap_y:.4}, Z {cap_z:.4}"
                            print(entry)
                            file.write(entry + '\n')
                        except IOError as e:
                            print(f"failed I/O (reading colorimetry): {e}")
    except IOError as e:
        print(f"failed IO (i1 ctor): {e}")
        return
    finally:
        if meter:
            del meter


if __name__ == "__main__":
    exercise_connected_i1pro(calibrate_only=True, wait_for_button_press=False)
