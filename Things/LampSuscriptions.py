class LampSuscriptions:

    def __init__(self):

        self.topicOn = []
        self.topicOff = []

    def newOn(self, newTopicOn):

        self.topicOn.append(newTopicOn)

    def newOff(self, newTopicOff):

        self.topicOff.append(newTopicOff)

    def remOn(self, remTopicOn):

        self.topicOn.remove(remTopicOn)

    def remOff(self, remTopicOff):

        self.topicOff.remove(remTopicOff)

    def containOn(self, contain):

        return contain in self.topicOn

    def containOff(self, contain):

        return contain in self.topicOff
