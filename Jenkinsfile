pipeline {
  agent any

  parameters {
    string(name: 'JOB_NAME', defaultValue: '', description: 'The upstream job name', trim: true)
  }

  environment {
    DOCKER_REGISTRY = 'docker.chameleoncloud.org'
    DOCKER_REGISTRY_CREDS = credentials('kolla-docker-registry-creds')
    SERVICE_NAME = """${sh(
      returnStdout: true,
      script: "echo '${params.JOB_NAME}' | cut -d/ -f1 | tr -d '\n'"
    )}"""
    SERVICE_BRANCH_NAME = """${sh(
      returnStdout: true,
      script: "echo '${params.JOB_NAME}' | cut -d/ -f2 | tr -d '\n'"
    )}"""
  }

  stages {
    stage('docker-setup') {
      steps {
        sh 'docker login --username=$DOCKER_REGISTRY_CREDS_USR --password=$DOCKER_REGISTRY_CREDS_PSW $DOCKER_REGISTRY'
      }
    }

    stage('build') {
      steps {
        copyArtifacts(projectName: "${params.JOB_NAME}",
                      target: "${env.WORKSPACE}/sdist",
                      selector: upstream(fallbackToLastSuccessful: true))
        sh "make ${env.SERVICE_NAME}-build"
      }
    }

    stage('publish') {
      steps {
        sh "make ${env.SERVICE_NAME}-publish"
      }
    }
  }

  post {
    always {
      sh 'docker logout $DOCKER_REGISTRY'
    }
  }
}
