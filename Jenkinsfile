pipeline{
    agent any
    environment{
        PYTHON_ENV="venv"
        SONARQUBE = 'sonarqube'
        NEXUS_CREDENTIALS = 'jenkins_nexus_sonarqube'
        NEXUS_URL = 'http://192.168.56.23:8081/repository/shopifyapp/'
    }
    stages {
        stage('Setup Python Environment') {
            steps {
                sh '''
                python3 -m venv ${PYTHON_ENV}
                . ${PYTHON_ENV}/bin/activate
                pip install --upgrade pip
                pip install -r requirements.txt
                '''
            }
        }

        stage('SonarQube Analysis') {
            environment {
                scannerHome = tool 'SonarQubeScanner'  // must match tool name in Jenkins config
            }
            steps {
                withSonarQubeEnv("${SONARQUBE}") {
                    sh '''
                    . ${PYTHON_ENV}/bin/activate
                    ${scannerHome}/bin/sonar-scanner \
                      -Dsonar.projectKey=shopify-flask \
                      -Dsonar.sources=src \
                      -Dsonar.host.url=$SONAR_HOST_URL \
                      -Dsonar.login=$SONAR_AUTH_TOKEN
                    '''
                }
            }
        }

        stage('Build Artifact') {
            steps {
                sh '''
                . ${PYTHON_ENV}/bin/activate
                python setup.py sdist
                '''
            }
        }

        stage('Upload to Nexus') {
            steps {
                sh '''
                ARTIFACT=$(ls dist/*.tar.gz)
                echo "Uploading $ARTIFACT to Nexus..."
                curl -u ${NEXUS_CREDENTIALS_USR}:${NEXUS_CREDENTIALS_PSW} \
                     --upload-file $ARTIFACT ${NEXUS_URL}
                '''
            }
        }
    }
}