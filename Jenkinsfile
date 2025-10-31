pipeline{
    agent any
    environment{
        PYTHON_ENV="venv"
        SONARQUBE = 'sonarqube'
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
                 . venv/bin/activate
                 pip install --upgrade pip setuptools wheel
                 python setup.py sdist
                 '''
                }
            }
         

       stage('Upload to Nexus') {
    steps {
        withCredentials([usernamePassword(credentialsId: 'jenkins_nexus_sonarqube', usernameVariable: 'NEXUS_USER', passwordVariable: 'NEXUS_PASS')]) {
            sh '''
                echo "Uploading artifacts to Nexus raw repository..."
                for file in dist/*; do
                    echo "Uploading $file ..."
                    curl -u $NEXUS_USER:$NEXUS_PASS \
                         --upload-file "$file" \
                         http://192.168.56.23:8081/repository/shopifyapp/
                done
            '''
        }
    }
}
    }

}





