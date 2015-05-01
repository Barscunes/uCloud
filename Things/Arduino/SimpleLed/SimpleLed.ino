int led=13, msg_from_python='2';

void setup() 
{
  Serial.begin(9600);  
  pinMode(led, OUTPUT);
  digitalWrite(led, LOW);
}

void loop() 
{
  if(Serial.available() > 0)
  {
    msg_from_python = Serial.read();
  }
  if (msg_from_python == '1')
    digitalWrite(led, HIGH);
  else if (msg_from_python == '0')
    digitalWrite(led, LOW);
}
  
