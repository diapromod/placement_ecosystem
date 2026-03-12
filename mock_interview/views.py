from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import InterviewSession, InterviewMessage
from matcher.models import JobDescription, Resume
from .services import InterviewManager
import json

interview_manager = InterviewManager()

@login_required
def index(request):
    all_sessions = InterviewSession.objects.filter(student=request.user).order_by('-created_at')
    active_sessions = all_sessions.filter(is_completed=False)
    completed_sessions = all_sessions.filter(is_completed=True)
    
    return render(request, 'mock_interview/index.html', {
        'active_sessions': active_sessions,
        'completed_sessions': completed_sessions
    })

@login_required
def delete_session(request, session_id):
    session = get_object_or_404(InterviewSession, id=session_id, student=request.user)
    session.delete()
    return redirect('mock_interview:index')

@login_required
def start_session(request):
    if request.method == "POST":
        jd_id = request.POST.get('jd_id')
        jd = get_object_or_404(JobDescription, id=jd_id)
        
        # Repair title if None
        if not jd.title or jd.title == "None":
            from matcher.utils import extract_job_title
            jd.title = extract_job_title(jd.raw_text) or "Career Interview"
            jd.save()

        # Create new session
        session = InterviewSession.objects.create(
            student=request.user,
            target_jd=jd
        )
        
        # Initial AI greeting/question
        resume = Resume.objects.filter(email=request.user.email).first()
        resume_text = resume.raw_text if resume else "Not available."
        
        first_question = interview_manager.get_next_question(session, [], jd.raw_text, resume_text)
        InterviewMessage.objects.create(session=session, sender='ai', content=first_question)
        
        return redirect('mock_interview:chat_view', session_id=session.id)
    
    jds = JobDescription.objects.all().order_by('-uploaded_at')
    return render(request, 'mock_interview/start.html', {'jds': jds})

@login_required
def chat_view(request, session_id):
    session = get_object_or_404(InterviewSession, id=session_id, student=request.user)
    
    # Repair title in existing session if needed
    if not session.target_jd.title or session.target_jd.title == "None":
        from matcher.utils import extract_job_title
        session.target_jd.title = extract_job_title(session.target_jd.raw_text) or "Career Interview"
        session.target_jd.save()

    if session.is_completed:
        return redirect('mock_interview:feedback_view', session_id=session.id)
        
    if request.method == "POST":
        user_response = request.POST.get('message')
        if user_response:
            is_manual_finish = user_response.strip().upper() == "__FINISH_NOW__"
            
            # Save user message if not a control signal
            if not is_manual_finish:
                InterviewMessage.objects.create(session=session, sender='user', content=user_response)
            
            msg_count = session.messages.filter(sender='user').count()
            
            # Check for completion (Manual or Auto at 10 turns)
            if is_manual_finish or msg_count >= 10:
                # PERSIST COMPLETION STATUS IMMEDIATELY to avoid hangs
                session.is_completed = True
                session.save(update_fields=['is_completed'])
                
                feedback_json = interview_manager.generate_feedback(session.messages.all(), session.target_jd.raw_text)
                session.feedback_summary = feedback_json
                
                # Attempt to extract score
                try:
                    data = json.loads(feedback_json)
                    session.overall_score = data.get('score')
                except:
                    pass
                
                session.save()
                return redirect('mock_interview:feedback_view', session_id=session.id)
            
            # Generate next AI question
            resume = Resume.objects.filter(email=request.user.email).first()
            resume_text = resume.raw_text if resume else "Not available."
            
            next_question = interview_manager.get_next_question(
                session, 
                session.messages.all(), 
                session.target_jd.raw_text, 
                resume_text
            )
            InterviewMessage.objects.create(session=session, sender='ai', content=next_question)
            
            return redirect('mock_interview:chat_view', session_id=session.id)
            
    messages = session.messages.all()
    # Logic for turn counting (based on user messages)
    user_turns = messages.filter(sender='user').count()
    return render(request, 'mock_interview/session.html', {
        'session': session,
        'messages': messages,
        'turn_count': user_turns + 1
    })

@login_required
def feedback_view(request, session_id):
    session = get_object_or_404(InterviewSession, id=session_id, student=request.user)
    
    # Safety: Ensure session is marked complete if we are viewing feedback
    if not session.is_completed:
        session.is_completed = True
        session.save()

    try:
        feedback = json.loads(session.feedback_summary)
    except:
        feedback = {"summary": session.feedback_summary}
        
    return render(request, 'mock_interview/feedback.html', {
        'session': session,
        'feedback': feedback
    })
