# from pkg_resources import require
# require("i1ProAdapter")


from meter.xrite.i1pro import I1Pro
from meter.meter_abstractions import Mode  # , IntegrationType, Observer


def measure():
    try:
        i1 = I1Pro()
    except IOError as e:
        print(f"failed IO (i1 ctor): {e}")
        return
    print(f"{i1.model()} s/n {i1.serial_number()}")
    print(f"using {i1.make()} SDK {i1.sdk_version()}")
    print(f"via EIEIO adapter {i1.adapter_version()}, Python driver {i1.driver_version()}")
    try:
        print("attempting to set emissive mode...", end='')
        i1.set_measurement_mode(Mode.emissive)
        print("emissive mode set.")
    except IOError as e:
        print(f"failed I/O (setting measurement mode): {e}")
        return
    try:
        prompt = "patch name ('exit' to exit): "
        with open("/var/tmp/mes.txt", "a") as file:
            while True:
                patch = input(prompt)
                if patch == 'exit':
                    break
                try:
                    print("attempting to trigger i1Pro...", end='')
                    i1.trigger_measurement()
                    print("triggered")
                except IOError as e:
                    print(f"failed I/O (triggering measurement): {e}")
                    return
                try:
                    cap_x, cap_y, cap_z = i1.read_colorimetry()
                    entry = f"{patch}: X {cap_x:.4f}, Y {cap_y:.4}, Z {cap_z:.4}"
                    print(entry)
                    file.write(entry + '\n')
                except IOError as e:
                    print(f"failed I/O (reading colorimetry): {e}")
    finally:
        print("in finally clause")
        if i1:
            del i1


if __name__ == "__main__":
    measure()
