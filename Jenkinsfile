@Library('jenkins-helpers@v0.1.8') _

podTemplate(
    label: 'jnlp-cognite-sdk-python',
    containers: [containerTemplate(name: 'python',
                                   image: 'python:3.6.4',
                                   command: '/bin/cat -',
                                    resourceRequestCpu: '1000m',
                                   resourceRequestMemory: '500Mi',
                                   resourceLimitCpu: '1000m',
                                   resourceLimitMemory: '500Mi',
                                   ttyEnabled: true)],
    volumes: [secretVolume(secretName: 'jenkins-docker-builder',
                           mountPath: '/jenkins-docker-builder',
                           readOnly: true)]) {
    node('jnlp-cognite-sdk-python') {
        def gitCommit
        container('jnlp') {
            stage('Checkout') {
                checkout(scm)
                gitCommit = sh(returnStdout: true, script: 'git rev-parse --short HEAD').trim()
            }
        }
        container('python') {
            stage('Install pipenv') {
                sh("pip3 install pipenv")
            }
            stage('Install dependencies') {
                sh("pipenv install")
                sh("pipenv run pip3 install .")
            }
            stage('Test') {
                sh("cd unit_tests && pipenv run python3 run_tests.py")
            }
            stage('Build docs') {
                sh("cd docs && make html")
            }
            stage('Build') {
                sh("pipenv run python3 setup.py sdist")
                sh("pipenv run python3 setup.py bdist_wheel")
            }
        }
    }
}