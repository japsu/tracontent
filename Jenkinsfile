def environmentMap = [
  "master": ["con2"],
  "premium": ["tracon"],
]

pipeline {
  agent any

  environment {
    PYTHONUNBUFFERED = "1"
    SKAFFOLD_DEFAULT_REPO = "harbor.con2.fi/con2"
  }

  stages {
    stage("Build") {
      steps {
        sh "emskaffolden -- build --file-output build.json"
      }
    }

    stage("Deploy") {
      steps {
        script {
          for (environmentName in environmentMap.get(env.BRANCH_NAME, [])) {
            sh "emskaffolden -E ${environmentName} -- deploy -n tracontent-${environmentName} -a build.json"
          }
        }
      }
    }
  }

  post {
    always {
      archiveArtifacts "build.json"
      archiveArtifacts "kubernetes/template.compiled.yaml"
    }
  }
}
