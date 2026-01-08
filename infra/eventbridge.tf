# EventBridge rule to trigger Lambda on schedule
# Runs every 10 minutes from 7am-9pm Pacific (15:00-04:30 UTC)
resource "aws_cloudwatch_event_rule" "schedule" {
  name                = "${var.project_name}-schedule"
  description         = "Trigger ski resort analyzer every 10 minutes during resort hours (7am-9pm Pacific)"
  schedule_expression = "cron(0,10,20,30,40,50 0-4,15-23 * * ? *)"
}

# EventBridge target
resource "aws_cloudwatch_event_target" "lambda" {
  rule      = aws_cloudwatch_event_rule.schedule.name
  target_id = "TriggerLambda"
  arn       = aws_lambda_function.analyzer.arn
}

# Permission for EventBridge to invoke Lambda
resource "aws_lambda_permission" "eventbridge" {
  statement_id  = "AllowEventBridgeInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.analyzer.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.schedule.arn
}
