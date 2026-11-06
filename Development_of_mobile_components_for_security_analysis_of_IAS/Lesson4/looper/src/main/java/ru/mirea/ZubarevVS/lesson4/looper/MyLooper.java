package ru.mirea.ZubarevVS.lesson4.looper;


import android.os.*;

/**
 * Владелец отдельной MessageQueue. Handler публикуется только после Looper.prepare().
 */
public class MyLooper extends Thread {
    // ПЕРЕМЕННАЯ: handler
    // Handler, связанный с MessageQueue фонового Looper.
    private volatile Handler handler;
    // ПЕРЕМЕННАЯ: main
    // Handler главного потока, получает результат для UI.
    private final Handler main;
    private final Runnable ready;

    public MyLooper(Handler main, Runnable ready) {
        super("Lesson4-Looper");
        this.main = main;
        this.ready = ready;
    }

    // ЗАЩИТА: getHandler
    // Возвращает Handler фонового Looper только после публикации volatile поля. Кнопка включается callback
    // ready после завершения Looper.prepare и создания Handler, что исключает обращение к null.
    public Handler getHandler() {
        // ПЕРЕМЕННАЯ: handler
        // Handler, связанный с MessageQueue фонового Looper.
        return handler;
    }

    @Override
    // ЗАЩИТА: run
    // Метод фонового Thread. Looper.prepare создаёт MessageQueue, Handler разбирает Bundle AGE/JOB и
    // передаёт ответ главному Handler, Looper.loop обслуживает очередь до quit. Результат дополнительно
    // фиксируется в Log.d.
    public void run() {
        Looper.prepare();
        handler = new Handler(Looper.myLooper(), msg -> {
            // ПЕРЕМЕННАЯ: age
            // Возраст пользователя; age*1000L задаёт задержку сообщения в миллисекундах.
            int age = msg.getData().getInt("AGE");
            // ПЕРЕМЕННАЯ: job
            // Введённая профессия/работа, передаётся в Bundle JOB.
            String job = msg.getData().getString("JOB", "");
            // sendMessageDelayed выдерживает возраст секунд, не блокируя UI/очередь sleep.
            // ПЕРЕМЕННАЯ: result
            // Контейнер/текст/поле результата согласно типу объявления и методу.
            String result = "Возраст: " + age + "; работа: " + job + "; задержка: " + age + " с";
            android.util.Log.d("MyLooper", "Task execute: " + result);
            Message reply = main.obtainMessage();
            Bundle bundle = new Bundle();
            bundle.putString("result", result);
            reply.setData(bundle);
            main.sendMessage(reply);
            return true;
        });
        main.post(ready);
        Looper.loop();
    }

    // ЗАЩИТА: quit
    // Завершает очередь фонового потока через quitSafely, если Handler уже создан. Поток не должен
    // бесконечно удерживать Activity после закрытия экрана.
    public void quit() {
        Handler h = handler;
        if (h != null) h.getLooper().quitSafely();
    }
}
