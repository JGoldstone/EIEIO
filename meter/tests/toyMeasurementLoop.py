from pkg_resources import require
require("i1ProAdapter")

import i1ProAdapter


def measure():
    i1ProAdapter.attach()
    i1ProAdapter.openConnection(False)
    i1ProAdapter.setMeasurementMode("emissive")
    print()
    prompt = "patch name ('exit' to exit): "
    with open("/var/tmp/mes.txt", "a") as file:
        while True:
            patch = input(prompt)
            if patch == 'exit':
                break
            i1ProAdapter.trigger()
            color = i1ProAdapter.measuredColorimetry()
            entry = "%s %.4f %.4f %.4f" % (patch, color[0], color[1], color[2])
            print(entry)
            file.write(entry + "\n")
        i1ProAdapter.closeConnection(False)
        i1ProAdapter.detach()


if __name__ == "__main__":
    measure()
