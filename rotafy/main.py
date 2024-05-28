from rotafy import manager
m = manager.Manager("test", "examples/basic.toml")
m.fill()
m.notify()
m.rota.print()
m.rota.pdf("basic_test.pdf")