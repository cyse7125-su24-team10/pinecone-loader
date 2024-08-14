pipeline {
    environment {
        registry = "vkneu7/pinecone-loader"
        DOCKER_ID = 'vkneu7'
        DOCKER_PWD = credentials('DOCKER_PWD')
        imageName = "pinecone-loader"
    }
    agent any
    stages {
        stage('Clone') {
            steps {
                git credentialsId: 'github-pat', branch: 'main', url: 'https://github.com/cyse7125-su24-team10/pinecone-loader.git'
            }
        }
        stage('Release') {
            steps {
                withCredentials([usernamePassword(credentialsId: 'github-pat', usernameVariable: 'GITHUB_USERNAME', passwordVariable: 'GITHUB_TOKEN')]) {
                    script {
                        sh "npx semantic-release"
                    }
                }
            }
        }
        stage('Build and Push') {
            steps {
                script {
                    def latestTag = sh(script: 'git describe --abbrev=0 --tags', returnStdout: true).trim()
                    echo "Using release tag: ${latestTag}"

                    sh 'echo $DOCKER_PWD | docker login -u $DOCKER_ID --password-stdin'
                    sh 'docker buildx rm newbuilderx || true'
                    sh 'docker buildx create --use --name newbuilderx --driver docker-container'
                    sh "docker buildx build --file Dockerfile --platform linux/amd64,linux/arm64 -t ${registry}:${latestTag} --push ."
                    sh 'docker buildx rm newbuilderx'
                }
            }
        }
    }
}