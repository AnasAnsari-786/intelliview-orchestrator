from workers.scoring_models import ExperimentalRiskModel, WeightedRiskModel


def _sample_results():
    return (
        {
            "confidence_score": 0.8,
            "suspicious_behavior": False,
        },
        {
            "confidence_score": 0.7,
            "suspicious_behavior": False,
        },
        {
            "score": 0.9,
        },
    )


def test_weighted_risk_model_generates_report():
    model = WeightedRiskModel()
    video_result, audio_result, evaluation_result = _sample_results()

    report = model.generate_report(
        session_id="test-session",
        video_result=video_result,
        audio_result=audio_result,
        evaluation_result=evaluation_result,
    )

    assert report["session_id"] == "test-session"
    assert report["model"] == model.name
    assert "final_risk_score" in report
    assert "risk_classification" in report
    assert "component_risks" in report


def test_experimental_risk_model_generates_report():
    model = ExperimentalRiskModel()
    video_result, audio_result, evaluation_result = _sample_results()

    report = model.generate_report(
        session_id="test-session",
        video_result=video_result,
        audio_result=audio_result,
        evaluation_result=evaluation_result,
    )

    assert report["session_id"] == "test-session"
    assert report["model"] == model.name
    assert "final_risk_score" in report
    assert "risk_classification" in report
    assert "component_risks" in report


def test_model_names_are_distinct():
    weighted = WeightedRiskModel()
    experimental = ExperimentalRiskModel()

    assert weighted.name != experimental.name
