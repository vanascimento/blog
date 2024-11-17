package handlers

import (
	"encoding/json"
	"fmt"
	"io"
	"net/http"

	"github.com/gin-gonic/gin"
	v1 "k8s.io/api/admission/v1"
	appsv1 "k8s.io/api/apps/v1"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
)

const MAX_CPU_VALUE int64 = 100 // 100m
const MAX_MEMORY_VALUE int64 = 250_000_000 // 250MB
const MAX_REPLICAS int32 = 2

// validateResourceContainers validates the CPU and memory resource requests of containers in a deployment.
// It checks if the CPU and memory values provided in the deployment's containers are within the allowed limits.
// If any of the values exceed the maximum limits, an error is returned.
// The function takes a deployment object as input and iterates over the containers in the deployment's template.
// It retrieves the CPU and memory values from the container's resource requests and compares them with the maximum limits.
// If any value exceeds the limit, an error message is returned with the corresponding resource type and value.
// If all values are within the limits, nil is returned.
func validateResourceContainers(deployment appsv1.Deployment) error {
	for _, container := range deployment.Spec.Template.Spec.Containers {
		cpuValue := container.Resources.Requests.Cpu().MilliValue()
		memoryValue := container.Resources.Requests.Memory().Value()
		if cpuValue > MAX_CPU_VALUE {
			return fmt.Errorf("cpu request is too high, the maximum value is %f and you provided %f", MAX_CPU_VALUE, cpuValue)
		}

		if memoryValue > MAX_MEMORY_VALUE {
			return fmt.Errorf("memory request is too high, the maximum value is %f and you provided %f", MAX_MEMORY_VALUE, memoryValue)
		}
	}
	return nil
}

// validateReplicasContainer validates the number of replicas in a deployment.
// It checks if the number of replicas provided in the deployment is within the allowed limit.
// If the number of replicas exceeds the maximum limit, an error is returned.
// The function takes a deployment object as input and compares the number of replicas with the maximum limit.
// If the number of replicas exceeds the limit, an error message is returned with the provided number of replicas and the maximum limit.
// If the number of replicas is within the limit, nil is returned.
func validateReplicasContainer(deployment appsv1.Deployment) error {
	if *deployment.Spec.Replicas > MAX_REPLICAS {
		return fmt.Errorf("the maximum number of replicas is %d and you provided %d", MAX_REPLICAS, *deployment.Spec.Replicas)
	}
	return nil
}

// admitRequest sets the admission response to allow the request.
// It takes an admission review object as input and sets the response to allowed with the same UID as the request.
// The modified admission review object is returned.
func admitRequest(admissionReview *v1.AdmissionReview) *v1.AdmissionReview {
	admissionReview.Response = &v1.AdmissionResponse{
		Allowed: true,
		UID:     admissionReview.Request.UID,
		Result: &metav1.Status{ 
			Status: "Success",
			 Message: "The deployment is valid",
		},
	}
	return admissionReview
}

func rejectRequest(admissionReview *v1.AdmissionReview, message string) *v1.AdmissionReview {
	admissionReview.Response = &v1.AdmissionResponse{
		Allowed: false,
		Result: &metav1.Status{ 
			Status: "Failure",
			Message: message,
		},
		UID: admissionReview.Request.UID,
	}

	return admissionReview;
}

// validateDeploymentHandler is the handler function for validating a deployment.
// It takes a Gin context as input and validates the deployment in the request body.
// If the deployment is valid, an admission review with allowed status is returned.
// If the deployment is invalid, an error response is returned.
func ValidateDeploymentHandler(context *gin.Context) {

	jsonAdmission, err := io.ReadAll(context.Request.Body)
	if err != nil {
		context.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	incomeAdmissionReview := &v1.AdmissionReview{}

	err = json.Unmarshal(jsonAdmission, incomeAdmissionReview)
	if err != nil {
		rejectedAdmissionReview := rejectRequest(incomeAdmissionReview, err.Error())
		context.JSON(http.StatusBadRequest, rejectedAdmissionReview)
		return
	}

	deployment := appsv1.Deployment{}
	err = json.Unmarshal(incomeAdmissionReview.Request.Object.Raw, &deployment)
	if err != nil {
	    rejectedAdmissionReview := rejectRequest(incomeAdmissionReview, err.Error())
		context.JSON(http.StatusBadRequest, rejectedAdmissionReview)
		return
	}

	err = validateResourceContainers(deployment)
	if err != nil {
		rejectedAdmissionReview := rejectRequest(incomeAdmissionReview, err.Error())
		context.JSON(http.StatusBadRequest, rejectedAdmissionReview)
		return
	}

	err = validateReplicasContainer(deployment)
	if err != nil {
		rejectedAdmissionReview := rejectRequest(incomeAdmissionReview, err.Error())
		context.JSON(http.StatusBadRequest, rejectedAdmissionReview)
		return
	}

	admimittedAdmissionReview := admitRequest(incomeAdmissionReview)
	context.JSON(http.StatusOK, admimittedAdmissionReview)
	return 
}