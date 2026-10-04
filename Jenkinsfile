pipeline {
    agent any

    options {
        skipDefaultCheckout(true)
        disableConcurrentBuilds()
        timeout(time: 10, unit: 'MINUTES')
    }

    stages {
        stage('Checkout') {
            steps {
                deleteDir()
                checkout scm
            }
        }

        stage('Install Dependencies') {
            steps {
                bat '"C:\\Python314\\python.exe" -m venv .venv'
                bat '".venv\\Scripts\\python.exe" -m pip install -r requirements.txt'
            }
        }

        stage('AI Diagnosis and Recovery') {
            steps {
                withCredentials([
                    string(
                        credentialsId: 'gemini-api-key',
                        variable: 'GEMINI_API_KEY'
                    )
                ]) {
                    bat '".venv\\Scripts\\python.exe" -u ai_recovery.py'
                }
            }
        }
    }

    post {
        always {
            archiveArtifacts(
                artifacts: 'reports/*',
                allowEmptyArchive: true
            )
        }
    }
}