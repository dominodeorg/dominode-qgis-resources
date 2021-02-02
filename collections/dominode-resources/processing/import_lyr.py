"""
Model exported as python.
Name : import vector layer
Group : DomiNode
With QGIS : 31603
"""

from qgis.core import QgsProcessing
from qgis.core import QgsProcessingAlgorithm
from qgis.core import QgsProcessingMultiStepFeedback
from qgis.core import QgsProcessingParameterExpression
from qgis.core import QgsProcessingParameterVectorLayer
from qgis.core import QgsProcessingParameterString
from qgis.core import QgsProcessingParameterBoolean
from qgis.core import QgsExpression
from qgis.core import QgsExpressionContextUtils, QgsProject
import processing
import psycopg2

class ImportVectorLayer(QgsProcessingAlgorithm):

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterExpression('dbconnectionnameexpression', 'DB connection name', parentLayerParameterName='', defaultValue=' @dominode_db_connection_name '))
        self.addParameter(QgsProcessingParameterVectorLayer('inputlayer', 'Input layer', types=[QgsProcessing.TypeVectorAnyGeometry], defaultValue=None))
        self.addParameter(QgsProcessingParameterString('layername', 'output table name', multiLine=False, defaultValue=''))
        self.addParameter(QgsProcessingParameterBoolean('VERBOSE_LOG', 'Verbose logging', optional=True, defaultValue=False))

    def processAlgorithm(self, parameters, context, model_feedback):
        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model
        feedback = QgsProcessingMultiStepFeedback(4, model_feedback)
        results = {}
        outputs = {}
        #config connection to db
        pg_service = QgsExpressionContextUtils.globalScope().variable("dominode_db_connection_name")
        connection = psycopg2.connect(service=pg_service)

        # Convert expression to string
        alg_params = {
            'INPUT': parameters['dbconnectionnameexpression']
        }
        outputs['ConvertExpressionToString'] = processing.run('script:expressiontostringconverter', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(1)
        if feedback.isCanceled():
            return {}

        # Validate resource name
        alg_params = {
            'INPUT_LAYER': '',
            'INPUT_NAME': parameters['layername']
        }
        outputs['ValidateResourceName'] = processing.run('script:resourcenamevalidator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(2)
        if feedback.isCanceled():
            return {}

        # Export to PostgreSQL (available connections)
        alg_params = {
            'ADDFIELDS': False,
            'APPEND': False,
            'A_SRS': None,
            'CLIP': False,
            'DATABASE': pg_service,
            'DIM': 0,
            'GEOCOLUMN': 'geom',
            'GT': '',
            'GTYPE': 0,
            'INDEX': False,
            'INPUT': parameters['inputlayer'],
            'LAUNDER': True,
            'OPTIONS': '',
            'OVERWRITE': True,
            'PK': 'id',
            'PRECISION': True,
            'PRIMARY_KEY': '',
            'PROMOTETOMULTI': False,
            'SCHEMA': outputs['ValidateResourceName']['OUTPUT_DB_STAGING_SCHEMA_NAME'],
            'SEGMENTIZE': '',
            'SHAPE_ENCODING': '',
            'SIMPLIFY': '',
            'SKIPFAILURES': False,
            'SPAT': None,
            'S_SRS': None,
            'TABLE': outputs['ValidateResourceName']['OUTPUT_DATASET_NAME'],
            'T_SRS': None,
            'WHERE': ''
        }
        outputs['ExportToPostgresqlAvailableConnections'] = processing.run('gdal:importvectorintopostgisdatabaseavailableconnections', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(3)
        if feedback.isCanceled():
            return {}

        # set staging permissions
        schema_out = outputs['ValidateResourceName']['OUTPUT_DB_STAGING_SCHEMA_NAME']
        table_out = outputs['ValidateResourceName']['OUTPUT_DATASET_NAME']
        query = "SELECT DomiNodeSetStagingPermissions('%s.\"%s\"')" % (schema_out,table_out)
        cursor = connection.cursor()
        cursor.execute(query)
        record = cursor.fetchone()
        cursor.close()
        return results

    def name(self):
        return 'import vector layer'

    def displayName(self):
        return 'import vector layer'

    def group(self):
        return 'DomiNode'

    def groupId(self):
        return 'DomiNode'

    def createInstance(self):
        return ImportVectorLayer()
