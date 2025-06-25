provider "aws" {
  region = "us-east-1"
}

resource "aws_instance" "example" {
  ami           = "ami-0c02fb55956c7d316"
  instance_type = "t2.micro"

  tags = {
    Name = "MyEC2Instance"
  }
}

output "instance_ip" {
  value = aws_instance.example.public_ip
}
