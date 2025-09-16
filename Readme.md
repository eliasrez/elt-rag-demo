Initialize Terraform and apply

cd infra/terraform
terraform init
terraform plan -out=tfplan
terraform apply tfplan


Run this in PowerShell or Bash (replace <SUBSCRIPTION_ID> with your own):

az ad sp create-for-rbac \
  --name "terraform-sp" \
  --role Contributor \
  --scopes /subscriptions/<SUBSCRIPTION_ID> \
  --sdk-auth
