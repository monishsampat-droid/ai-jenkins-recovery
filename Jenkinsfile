pipeline {
    agent any

    options {
        skipDefaultCheckout(true)
        disableConcurrentBuilds()
        timeout(time: 10, unit: 'MINUTES')
    }

    parameters {
        booleanParam(
            name: 'ENABLE_AI_RECOVERY',
            defaultValue: true,
            description: 'Automatically diagnose and repair the test-folder error using AI'
        )
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

        stage('Run Tests and Optional AI Recovery') {
            steps {
                script {
                    if (params.ENABLE_AI_RECOVERY) {
                        withCredentials([
                            string(
                                credentialsId: 'gemini-api-key',
                                variable: 'GEMINI_API_KEY'
                            )
                        ]) {
                            bat '".venv\\Scripts\\python.exe" -u ai_recovery.py'
                        }
                    } else {
                        bat '".venv\\Scripts\\python.exe" -u ai_recovery.py --no-ai'
                    }
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