pipeline {
    agent { label 'docker-linux' }
    options {
        skipDefaultCheckout(true)
        disableConcurrentBuilds()
        timeout(time: 30, unit: 'MINUTES')
        buildDiscarder(logRotator(numToKeepStr: '10'))
    }
    parameters {
        string(name: 'APP_PORT', defaultValue: '8081', description: 'Локальный порт приложения на Jenkins-агенте')
    }
    stages {
        stage('Получить исходники из GitHub') {
            steps { checkout scm }
        }
        stage('Проверить окружение') {
            steps {
                script {
                    if (!(params.APP_PORT ==~ /[0-9]{4,5}/) || params.APP_PORT.toInteger() < 1024 || params.APP_PORT.toInteger() > 65535) {
                        error('APP_PORT должен быть числом от 1024 до 65535')
                    }
                    def revision = sh(script: 'git rev-parse --short=12 HEAD', returnStdout: true).trim()
                    env.REPAIR_IMAGE = "repair-tracker:build-${env.BUILD_NUMBER}-${revision}"
                    env.APP_PORT = params.APP_PORT
                }
                sh 'docker version && docker compose version && python3 --version'
            }
        }
        stage('Собрать Docker-образ и выполнить тесты') {
            steps { sh 'docker build --pull --tag "$REPAIR_IMAGE" .' }
        }
        stage('Запустить контейнер') {
            steps {
                sh '''
                    set -eu
                    docker compose --project-name repair-tracker-ci -f ci/compose.yaml up -d --wait --wait-timeout 120 --no-build --pull never
                    docker compose --project-name repair-tracker-ci -f ci/compose.yaml ps
                '''
            }
        }
        stage('Проверить приложение') {
            steps { sh 'python3 ci/check_health.py "http://127.0.0.1:$APP_PORT/health"' }
        }
    }
    post {
        success { echo 'Образ собран, тесты пройдены, контейнер работает на Jenkins-агенте.' }
        failure {
            sh '''
                docker compose --project-name repair-tracker-ci -f ci/compose.yaml ps || true
                docker compose --project-name repair-tracker-ci -f ci/compose.yaml logs --tail=60 || true
            '''
        }
    }
}
