package main

import (
	"github.com/gin-gonic/gin"
	"github.com/vanascimento/k8s_admission_webhook/handlers"
)

func main() {
  r := gin.Default()
  r.POST("/admission-deployment", handlers.ValidateDeploymentHandler)
  r.Run() 
}