import docker
import os

def list_comp():
    return


client = docker.from_env()


def run_pn_dev(path):
    print(path)
    image, logs = client.images.build(path = path)
    print(logs)
    container = client.containers.run(
        image=image.id,
        command="bash",
        name="pnet-hw-sensor",
        # network="my_macvlan",
        stdin_open=True,   # -i
        tty=True,          # -t
        auto_remove=True,  # --rm
        detach=True,
    )

    print(container.name)

    print(type(image))

    container.kill()

    return 0    


    
