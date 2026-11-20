#Nombre: Tomás Olmos Vásquez#
pipeline {
    agent any

    environment {
        IMAGE_NAME   = "securedev-flask"
        CONTAINER_STG = "flask-staging"
        CONTAINER_PRD = "flask-prod"
        DOCKER_NET   = "devsecops-net"
    }

    stages {
        stage('1. Construcción (Build)') {
            steps {
                echo '=== Construyendo imagen Docker de SecureDev ==='
                sh 'docker build -t ${IMAGE_NAME}:${BUILD_NUMBER} -t ${IMAGE_NAME}:latest .'
            }
        }

        stage('2. Pruebas (SCA + DAST con OWASP ZAP)') {
            steps {
                echo '=== 2.1 Auditoría de Dependencias (SCA) ==='
                sh '''
                    docker run --rm ${IMAGE_NAME}:${BUILD_NUMBER} sh -c "pip install -q pip-audit && pip-audit -r requirements.txt" || true
                '''

                echo '=== 2.2 Pruebas de Seguridad Automatizadas (OWASP ZAP) ==='
                sh '''
                    # Limpiar contenedor temporal previo si existe
                    docker rm -f ${CONTAINER_STG} || true

                    # Levantar app en entorno de pruebas dentro de la red compartida
                    docker run -d --name ${CONTAINER_STG} --network ${DOCKER_NET} ${IMAGE_NAME}:${BUILD_NUMBER}
                    sleep 4

                    # Preparar carpeta de reportes con permisos de escritura para ZAP
                    mkdir -p zap-reports
                    chmod 777 zap-reports

                    # Ejecutar OWASP ZAP Baseline Scan apuntando al endpoint /hello?name=test
                    docker run --rm --network ${DOCKER_NET} \
                        -v "${WORKSPACE}/zap-reports:/zap/wrk:rw" \
                        ghcr.io/zaproxy/zaproxy:stable zap-baseline.py \
                        -t http://${CONTAINER_STG}:5000/hello?name=test \
                        -r zap_report.html \
                        -w zap_report.md || true

                    # Detener y eliminar el contenedor de pruebas
                    docker rm -f ${CONTAINER_STG} || true
                '''
            }
            post {
                always {
                    publishHTML(target: [
                        allowMissing: true,
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
                echo '=== Desplegando contenedor en Producción (puerto 5001) ==='
                sh '''
                    docker rm -f ${CONTAINER_PRD} || true
                    docker run -d --name ${CONTAINER_PRD} --network ${DOCKER_NET} -p 5001:5000 --restart unless-stopped ${IMAGE_NAME}:${BUILD_NUMBER}
                '''
            }
        }
    }
}