from time import sleep

from batou.component import Component


class Takeslongtime(Component):
    def verify(self):
        sleep(2)
