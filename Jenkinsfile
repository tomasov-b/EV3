pipeline {
    agent any

    environment {
        IMAGE_NAME    = "securedev-flask"
        CONTAINER_STG = "flask-staging"
        CONTAINER_PRD = "flask-prod"
        DOCKER_NET    = "devsecops-net"
    }

    stages {
        stage('1. Construcción (Build)') {
            steps {
                echo '=== Construyendo imagen Docker endurecida de SecureDev ==='
                sh 'docker build -t ${IMAGE_NAME}:${BUILD_NUMBER} -t ${IMAGE_NAME}:latest .'
            }
        }

        stage('2. Pruebas (SCA + DAST con OWASP ZAP)') {
            steps {
                echo '=== 2.1 Auditoría de Dependencias (SCA) ==='
                sh '''
                    docker run --rm -u root ${IMAGE_NAME}:${BUILD_NUMBER} sh -c "pip install -q pip-audit && pip-audit -r requirements.txt"
                '''

                echo '=== 2.2 Pruebas de Seguridad Automatizadas (OWASP ZAP) ==='
                sh '''
                    docker rm -f ${CONTAINER_STG} zap-scanner || true
                    docker volume rm zap-wrk || true

                    # Levantar app endurecida en staging
                    docker run -d --name ${CONTAINER_STG} ${IMAGE_NAME}:${BUILD_NUMBER}
                    sleep 5
                    docker logs ${CONTAINER_STG}

                    mkdir -p zap-reports

                    # Ejecutar OWASP ZAP contra la versión corregida
                    docker run --name zap-scanner --network container:${CONTAINER_STG} -u root \
                        -v zap-wrk:/zap/wrk \
                        ghcr.io/zaproxy/zaproxy:stable zap-baseline.py \
                        -t http://127.0.0.1:5000/hello?name=test \
                        -r zap_report.html \
                        -w zap_report.md || true

                    docker cp zap-scanner:/zap/wrk/zap_report.html zap-reports/zap_report.html
                    docker cp zap-scanner:/zap/wrk/zap_report.md zap-reports/zap_report.md

                    docker rm -f ${CONTAINER_STG} zap-scanner || true
                    docker volume rm zap-wrk || true
                '''
            }
            post {
                always {
                    publishHTML(target: [
                        allowMissing: false,
                        alwaysLinkToLastBuild: true,
                        keepAll: true,
                        reportDir: 'zap-reports',
                        reportFiles: 'zap_report.html',
                        reportName: 'Reporte Seguridad OWASP ZAP'
                    ])
                }
            }
        }

        stage('3. Despliegue (Deploy Producción)') {
            steps {
                echo '=== Desplegando contenedor endurecido en Producción (puerto 5001) ==='
                sh '''
                    docker rm -f ${CONTAINER_PRD} || true
                    docker run -d --name ${CONTAINER_PRD} --network ${DOCKER_NET} -p 5001:5000 \
                        --restart unless-stopped ${IMAGE_NAME}:${BUILD_NUMBER}
                '''
            }
        }
    }
}