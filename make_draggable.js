(function(){
    window.dash_clientside = Object.assign({}, window.dash_clientside, {
        clientside: {
            make_draggable: function() {
                interact('.draggable-button').draggable({
                    listeners: {
                        move(event) {
                            var target = event.target;
                            var buttonId = target.getAttribute('data-id');
                            if (!buttonId) {
                                console.error('buttonId is null');
                                return;
                            }

                            var x = (parseFloat(target.getAttribute('data-x')) || 0) + event.dx;
                            var y = (parseFloat(target.getAttribute('data-y')) || 0) + event.dy;

                            // Translate the element
                            target.style.transform = 'translate(' + x + 'px, ' + y + 'px)';

                            // Update the position attributes
                            target.setAttribute('data-x', x);
                            target.setAttribute('data-y', y);

                            // Prepare the data to be sent to the server
                            var storeData = {};
                            storeData[buttonId] = {
                                x: x,
                                y: y,
                                width: parseFloat(target.style.width),
                                height: parseFloat(target.style.height)
                            };

                            // Send the data to the Flask server via POST request
                            fetch('/update_button_positions', {
                                method: 'POST',
                                headers: {
                                    'Content-Type': 'application/json'
                                },
                                body: JSON.stringify(storeData)
                            })
                            .then(response => response.json())
                            .then(data => {
                                if (!data.success) {
                                    console.error('Server error:', data.error);
                                } else {
                                    console.log('Success:', data);
                                }
                            })
                            .catch((error) => console.error('Error:', error));
                        }
                    }
                }).resizable({
                    edges: { left: true, right: true, bottom: true, top: true }
                }).on('resizemove', function(event) {
                    var target = event.target;
                    var buttonId = target.getAttribute('data-id');
                    if (!buttonId) {
                        console.error('buttonId is null.');
                        return;
                    }

                    var x = (parseFloat(target.getAttribute('data-x')) || 0);
                    var y = (parseFloat(target.getAttribute('data-y')) || 0);

                    // Update the element's style
                    target.style.width = event.rect.width + 'px';
                    target.style.height = event.rect.height + 'px';

                    // Translate when resizing from top or left edges
                    x += event.deltaRect.left;
                    y += event.deltaRect.top;

                    target.style.transform = 'translate(' + x + 'px, ' + y + 'px)';

                    target.setAttribute('data-x', x);
                    target.setAttribute('data-y', y);

                    // Prepare the data to be sent to the server
                    var storeData = {};
                    storeData[buttonId] = {
                        x: x,
                        y: y,
                        width: event.rect.width,
                        height: event.rect.height
                    };

                    // Send the data to the Flask server via POST request
                    fetch('/update_button_positions', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify(storeData)
                    })
                    .then(response => response.json())
                    .then(data => {
                        if (!data.success) {
                            console.error('Server error:', data.error);
                        } else {
                            console.log('Success:', data);
                        }
                    })
                    .catch((error) => console.error('Error:', error));
                });

                return '';
            }
        }
    });
})();
