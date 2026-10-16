import jenkins.model.Jenkins

def controller = Jenkins.get()
controller.setNumExecutors(1)
controller.setLabelString('docker-linux')
controller.save()
