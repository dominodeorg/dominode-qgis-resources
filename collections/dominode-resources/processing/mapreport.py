# -*- coding: utf-8 -*-

"""
***************************************************************************
*                                                                         *
*   This program is free software; you can redistribute it and/or modify  *
*   it under the terms of the GNU General Public License as published by  *
*   the Free Software Foundation; either version 2 of the License, or     *
*   (at your option) any later version.                                   *
*                                                                         *
***************************************************************************
"""

from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import (QgsProject,
                       QgsLayerTreeModel,
                       QgsMapLayer,
                       QgsProcessing,
                       QgsProcessingException,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterFileDestination)
from qgis import processing
import os
import json
from datetime import date

# Pollute the global namespace with current project variables
project_home = QgsProject.instance().readPath("./")
project_home = os.path.abspath(project_home)
current_project_name = QgsProject.instance().baseName()
current_project_file = QgsProject.instance().fileName()

class DomiNodeTopoProjectReportAlgorithm(QgsProcessingAlgorithm):
    """
    Generate a map report
    """

    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.

    # INPUT = 'INPUT'
    # OUTPUT = 'OUTPUT'
    TEXT_REPORT = 'TEXT_REPORT'
    JSON_REPORT = 'JSON_REPORT'

    def tr(self, string):
        """
        Returns a translatable string with the self.tr() function.
        """
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return DomiNodeTopoProjectReportAlgorithm()

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'dominodetopoprojectreportscript'

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr('Topomap Project Report Script')

    def group(self):
        """
        Returns the name of the group this algorithm belongs to. This string
        should be localised.
        """
        return self.tr('DomiNode')

    def groupId(self):
        """
        Returns the unique ID of the group this algorithm belongs to. This
        string should be fixed for the algorithm, and must not be localised.
        The group id should be unique within each provider. Group id should
        contain lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'dominode'

    def shortHelpString(self):
        """
        Returns a localised short helper string for the algorithm. This string
        should provide a basic description about what the algorithm does and the
        parameters and outputs associated with it..
        """
        return self.tr("Report data generator for DomiNode topographic map projects")

    def initAlgorithm(self, config=None):
        """
        Here we define the inputs and output of the algorithm, along
        with some other properties.
        """

        self.addParameter(
            QgsProcessingParameterFileDestination(
                self.TEXT_REPORT,
                self.tr('Output project report'),
                defaultValue = os.path.join(project_home,str(current_project_name + '.mapreport.txt'))
            )
        )

        #self.addParameter(
        #    QgsProcessingParameterFileDestination(
        #        self.JSON_REPORT,
        #        self.tr('Output report data'),
        #        defaultValue = os.path.join(project_home,str(current_project_name + '.mapreport.json'))
        #    )
        #)

    def processAlgorithm(self, parameters, context, feedback):
        """
        Here is where the processing itself takes place.
        """

        report_date = date.today().strftime("%d %B %Y")
        text_file = self.parameterAsString(parameters, self.TEXT_REPORT, context)
        #json_file = self.parameterAsString(parameters, self.JSON_REPORT, context)

        project = QgsProject.instance()
        # alternatively, we could create a new instance from a fileproject = QgsProject
        # project.read('C:/path/file.qgs')

        themes = project.mapThemeCollection()

        # By rights we should be creating a theme that makes a "snapshot" of the
        # current project state so that we can reset it after the algorithm runs.
        # mapThemeRecord = QgsMapThemeCollection.createThemeFromCurrentState(
        #     QgsProject.instance().layerTreeRoot(),
        #     iface.layerTreeView().model()
        # )
        # temporary_theme_name = 'map_report_temporary_theme'
        # themes.insert(temporary_theme_name, mapThemeRecord)

        theme_names = themes.mapThemes()
        root = project.layerTreeRoot()
        model = QgsLayerTreeModel(root)
        results = json.loads('{}')
        for theme in theme_names:

            if feedback.isCanceled():
                return {}

            themes.applyTheme(theme, root, model)
            theme_results = list_active_layers(project, feedback)
            results[theme] = theme_results

        # themes.removeMapTheme(temporary_theme_name, mapThemeRecord)

        #with open(json_file, "w") as output_file:
        #    json.dump(results, output_file)

        with open(text_file, "w") as output_file:
            output_file.write('# DomiNode Topographic Map Report\n')
            output_file.write('\nReport date: {0}\n'.format(report_date))
            output_file.write('Project file: {0}\n'.format(project.fileName()))
            output_file.write('Last modified: {0}\n'.format(project.lastModified().toString()))
            for theme, layers in results.items():
                output_file.write('\n## {0}\n'.format(theme))
                for layer in layers:
                    output_file.write('- {0}\n'.format(layer))

        return {self.JSON_REPORT: results}

def list_active_layers(project, feedback):
    """
    Generate a list of visible layers. Currently only expects to encounter
    vector and raster types from designed DomiNode sources for topomaps and
    does not allow for the inclusion of other types such as mesh/ WFS etc.
    """

    results = []
    for layer in project.mapLayers().values():

        if feedback.isCanceled():
            return {}

        if project.layerTreeRoot().findLayer(layer.id()).isVisible():
            if layer.type() == QgsMapLayer.VectorLayer:
                # currently only expecting layers from postgres database
                layer_name = layer.dataProvider().uri().table()
                results.append(layer_name)
            elif layer.type() == QgsMapLayer.RasterLayer:
                # currently only expecting layers from minio/ S3 datastore
                layer_name = os.path.basename(layer.source())
                results.append(layer_name)

    return results
