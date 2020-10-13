import typing

from qgis.core import (
    QgsProcessingAlgorithm,
    QgsProcessingParameterExpression,
    QgsProcessingOutputString,
)
from qgis.PyQt.QtCore import QCoreApplication


class NoopValidator(QgsProcessingAlgorithm):

    INPUT = 'INPUT'
    OUTPUT = 'OUTPUT'

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return NoopValidator()

    def name(self):
        """
        Returns the unique algorithm name.
        """
        return 'noopvalidator'

    def displayName(self):
        """
        Returns the translated algorithm name.
        """
        return self.tr('Always returns True')

    def group(self):
        """
        Returns the name of the group this algorithm belongs to.
        """
        return self.tr('DomiNode')

    def groupId(self):
        """
        Returns the unique ID of the group this algorithm belongs
        to.
        """
        return 'dominode'

    def shortHelpString(self):
        """
        Returns a localised short help string for the algorithm.
        """
        return self.tr(
            'Algorithm that always returns true,'
            'It is intended to be used in validation '
            'of DomiNode legacy datasets.'
        )

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterExpression(
                self.INPUT,
                self.tr('Input'),
                optional=True
            )
        )
        self.addOutput(
            QgsProcessingOutputString(
                self.OUTPUT,
                self.tr('True value')
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        return {
            self.OUTPUT: True
        }
