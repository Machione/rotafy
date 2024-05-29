from rotafy.api import manager
m = manager.Manager("examples/basic.toml")
m.fill()
m.notify()
m.rota.print()
m.rota.pdf("basic_test.pdf")